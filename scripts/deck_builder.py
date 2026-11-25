#!/usr/bin/env python3
"""Constrained deck optimizer — pool-first deck generation with wildcard budget.

Single CLI entrypoint for generating Arena-importable Standard (60-card) and
Ranked Brawl (100-card) decks strictly from the user's owned pool.

Usage:
    python scripts/deck_builder.py --format standard --archetype midrange
    python scripts/deck_builder.py --format brawl --commander "Delney, Streetwise Lookout"
    python scripts/deck_builder.py --format standard --archetype control --max-wildcards 10
    python scripts/deck_builder.py --format brawl --commander "..." --max-wildcards 20

Pipeline:
  1. Load enriched pool (pool_enricher.py output) with functional roles + synergy
  2. Load archetype blueprint (archetypes.py)
  3. Filter candidates: owned_qty > 0 (hard constraint), format-legal, color-identity
  4. Score: RoleFit + OracleSynergy + CurveNeed + ManaEfficiency
  5. Greedy build → local-swap optimizer to satisfy quotas/curve/mana
  6. Auto-validate via scripts/deck_check.py
  7. Output Arena-importable list + Oracle-grounded rationale
  8. Optional: Monte Carlo goldfish simulation via scripts/deck_sim.py

Defaults to pool-first (owned_only). Use --max-wildcards to allow unowned cards.
"""

import argparse
import json
import os
import sys
import subprocess
import tempfile
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

# Allow importing sibling scripts
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from archetypes import get_blueprint, list_blueprints, ROLES
from mana_solver import color_source_requirements, solve_land_base, validate_mana_base

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ENRICHED_POOL = os.path.join(HERE, "enriched_pool.json")
POOL = os.path.join(ROOT, "pool.json")
DECKS_DIR = os.path.join(ROOT, "decks")

BASICS = {
    "plains", "island", "swamp", "mountain", "forest", "wastes",
    "snow-covered plains", "snow-covered island", "snow-covered swamp",
    "snow-covered mountain", "snow-covered forest", "snow-covered wastes",
}

XCOST_RE = __import__("re").compile(r"\{X\}")


def norm(name):
    import unicodedata
    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


def load_enriched_pool() -> dict:
    """Load enriched pool, falling back to pool.json if enriched not available."""
    if os.path.exists(ENRICHED_POOL):
        with open(ENRICHED_POOL, encoding="utf-8") as fh:
            data = json.load(fh)
        return data["pool"]
    # Fallback: load pool.json and enrich minimally
    with open(POOL, encoding="utf-8") as fh:
        data = json.load(fh)
    pool = data["pool"]
    # Add minimal enriched fields
    for name, entry in pool.items():
        entry.setdefault("functional_roles", [])
        entry.setdefault("synergy_features", {})
        entry.setdefault("oracle_text", entry.get("oracle_text", ""))
    return pool


def is_basic_land(name):
    return norm(name) in BASICS


def is_land(card):
    tl = (card.get("type_line") or "").lower()
    return "land" in tl


def printed_mv(mana_cost):
    """Mana value from printed cost (not Scryfall cmc)."""
    if not mana_cost:
        return 0
    total = 0
    for sym in __import__("re").findall(r"\{([^}]+)\}", mana_cost):
        if sym.isdigit():
            total += int(sym)
        elif sym.upper() in ("X", "Y", "Z"):
            continue  # variable, contributes 0 to minimum cost
        else:
            total += 1
    return total


def color_pips(mana_cost, color):
    """Count colored pips of a given color in mana cost."""
    if not mana_cost:
        return 0
    import re
    return len(re.findall(r"\{" + color + r"\}", mana_cost))


def score_card(card, blueprint, deck_state, pool_cards):
    """Score a candidate card for inclusion.

    Score = RoleFit + OracleSynergy + CurveNeed + ManaEfficiency
    All components normalized 0-1.
    """
    roles = set(card.get("functional_roles", []))
    synergy = card.get("synergy_features", {})

    # --- RoleFit: how well does this card fill unmet role quotas? ---
    role_fit = 0.0
    role_count = 0
    for role in roles:
        if role in blueprint.role_quotas:
            mn, mx = blueprint.role_quotas[role]
            current = deck_state["role_counts"].get(role, 0)
            target = blueprint.role_target_count(role)
            if current < target:
                # Higher score for roles we still need
                deficit = target - current
                role_fit += min(1.0, deficit / max(1, target))
                role_count += 1
    if role_count > 0:
        role_fit /= role_count

    # --- OracleSynergy: synergy features matching archetype theme ---
    synergy_score = 0.0
    syn_count = 0
    # Cards that generate tokens are good for token-maker archetypes
    if synergy.get("token_maker") or "token_maker" in roles:
        synergy_score += 0.3
        syn_count += 1
    if synergy.get("graveyard"):
        synergy_score += 0.2
        syn_count += 1
    if synergy.get("counters"):
        synergy_score += 0.2
        syn_count += 1
    if synergy.get("card_type_triggers"):
        synergy_score += 0.2
        syn_count += 1
    # Tribe synergy: if deck already has cards of same tribe, bonus
    tribes = synergy.get("tribes", [])
    if tribes:
        tribe_bonus = 0.0
        for tribe in tribes:
            tribe_count = deck_state["tribe_counts"].get(tribe, 0)
            tribe_bonus += min(0.3, tribe_count * 0.1)
        synergy_score += min(0.5, tribe_bonus)
        syn_count += 1
    if syn_count > 0:
        synergy_score /= syn_count

    # --- CurveNeed: does this mana value fit the curve target? ---
    mv = printed_mv(card.get("mana_cost") or "")
    if is_land(card):
        curve_need = 0.0  # lands handled by mana_solver
    else:
        target_frac = blueprint.curve_targets.get(mv, 0.0)
        current_count = deck_state["curve_counts"].get(mv, 0)
        total_spells = deck_state["total_spells"]
        current_frac = current_count / max(1, total_spells)
        # Score higher if we're below target
        if target_frac > 0:
            curve_need = max(0.0, min(1.0, (target_frac - current_frac) / target_frac))
        else:
            curve_need = 0.1  # low but non-zero for off-curve cards

    # --- ManaEfficiency: lower MV = higher efficiency (generally) ---
    if mv <= 2:
        mana_eff = 1.0
    elif mv <= 3:
        mana_eff = 0.7
    elif mv <= 4:
        mana_eff = 0.4
    elif mv <= 5:
        mana_eff = 0.2
    else:
        mana_eff = 0.1

    # --- Owned bonus: prefer cards we already own ---
    owned_qty = card.get("qty", 0)
    owned_bonus = min(0.2, owned_qty * 0.05)  # up to +0.2 for owning 4 copies

    # Weighted sum
    score = (
        0.35 * role_fit +
        0.25 * synergy_score +
        0.25 * curve_need +
        0.15 * mana_eff +
        owned_bonus
    )
    return score


def filter_candidates(
    pool: dict,
    blueprint,
    owned_only: bool,
    max_wildcards: int,
    commander_name: Optional[str] = None,
) -> List[dict]:
    """Filter pool cards to legal candidates for this format/blueprint."""
    candidates = []

    # Determine allowed color identity
    if commander_name and blueprint.format == "brawl":
        # Commander's color identity restricts the deck
        commander_card = pool.get(commander_name)
        if not commander_card:
            print(f"WARNING: Commander '{commander_name}' not found in pool", file=sys.stderr)
        else:
            ci = set(commander_card.get("color_identity", []) or [])
            blueprint.commander_identity = sorted(ci)

    allowed_ci = set(blueprint.commander_identity or [])

    for name, card in pool.items():
        qty = card.get("qty", 0)

        # Hard constraint: must be owned (qty > 0) unless wildcard budget allows
        if owned_only and qty <= 0:
            continue

        # Format legality
        fmt = blueprint.format
        legality = card.get(fmt)
        if legality != "legal":
            continue

        # Brawl: exactly one commander, it must be legendary creature/planeswalker
        if fmt == "brawl" and commander_name:
            if name == commander_name:
                continue  # commander added separately
        if fmt == "standard" and card.get("standard") != "legal":
            continue

        # Color identity check (Brawl)
        if fmt == "brawl" and allowed_ci:
            card_ci = set(card.get("color_identity", []) or [])
            if not card_ci <= allowed_ci:
                continue

        candidates.append(card)

    return candidates


def greedy_build(
    candidates: List[dict],
    blueprint,
    max_wildcards: int,
    owned_only: bool,
    pool: dict,
) -> Tuple[List[dict], dict]:
    """Greedy construction: pick highest-scoring cards until deck is full."""
    deck_state = {
        "role_counts": defaultdict(int),
        "curve_counts": defaultdict(int),
        "tribe_counts": defaultdict(int),
        "total_spells": 0,
        "total_lands": 0,
        "total_cards": 0,
        "wildcards_used": defaultdict(int),
    }

    selected: List[dict] = []
    remaining = list(candidates)

    # Sort by initial score
    remaining.sort(key=lambda c: -score_card(c, blueprint, deck_state, pool))

    target_non_land = blueprint.total_cards() - blueprint.land_target
    target_lands = blueprint.land_target

    # First pass: pick non-land spells
    spell_candidates = [c for c in remaining if not is_land(c)]
    land_candidates = [c for c in remaining if is_land(c)]

    i = 0
    while deck_state["total_cards"] < target_non_land and i < len(spell_candidates):
        card = spell_candidates[i]
        i += 1
        qty_owned = card.get("qty", 0)
        max_copies = 4 if blueprint.format == "standard" else 1
        if not card.get("any_number", False):
            max_copies = 1 if blueprint.format == "brawl" else 4
            # Basics are unlimited, handled separately

        # How many can we add?
        can_add = max_copies - sum(1 for s in selected if norm(s["name"]) == norm(card["name"]))
        if can_add <= 0:
            continue

        # Check wildcard budget
        need = max(0, 1 - qty_owned)  # need 1 copy
        if need > 0 and owned_only:
            continue  # can't afford

        # Add one copy
        selected.append(dict(card, qty_to_play=1))
        deck_state["total_cards"] += 1

        # Update state
        for role in card.get("functional_roles", []):
            deck_state["role_counts"][role] += 1
        mv = printed_mv(card.get("mana_cost") or "")
        deck_state["curve_counts"][mv] += 1
        deck_state["total_spells"] += 1
        for tribe in card.get("synergy_features", {}).get("tribes", []):
            deck_state["tribe_counts"][tribe] += 1

        # Re-sort remaining by updated score (recompute periodically)
        if deck_state["total_cards"] % 10 == 0:
            spell_candidates[i:] = sorted(
                spell_candidates[i:],
                key=lambda c: -score_card(c, blueprint, deck_state, pool)
            )

    # Second pass: add lands via mana_solver
    # Compute color requirements from selected spells
    spell_dicts = [{"name": s["name"], "color_identity": s.get("color_identity", []),
                    "mana_cost": s.get("mana_cost", ""), "cmc": s.get("cmc", 0),
                    "qty": s.get("qty_to_play", 1)} for s in selected]

    color_reqs = color_source_requirements(spell_dicts, blueprint.total_cards())

    # Prepare owned lands list
    owned_lands = [c for c in land_candidates if c.get("qty", 0) > 0]

    selected_lands, unmet = solve_land_base(
        color_reqs, owned_lands, blueprint.total_cards(), target_lands
    )

    for land in selected_lands:
        qty_to_play = land.get("qty_to_play", 0)
        if qty_to_play > 0:
            land_copy = dict(land)
            land_copy["qty_to_play"] = qty_to_play
            selected.append(land_copy)
            deck_state["total_lands"] += qty_to_play
            deck_state["total_cards"] += qty_to_play

    deck_state["color_requirements"] = color_reqs
    deck_state["unmet_mana"] = unmet

    return selected, deck_state


def local_swap_optimize(
    selected: List[dict],
    deck_state: dict,
    blueprint,
    candidates: List[dict],
    pool: dict,
    iterations: int = 200,
) -> Tuple[List[dict], dict]:
    """Local-swap optimization: try replacing cards to better satisfy quotas/curve."""
    import random
    random.seed(42)  # deterministic

    best_selected = list(selected)
    best_state = {
        "role_counts": dict(deck_state["role_counts"]),
        "curve_counts": dict(deck_state["curve_counts"]),
        "tribe_counts": dict(deck_state["tribe_counts"]),
        "total_spells": deck_state["total_spells"],
        "total_lands": deck_state["total_lands"],
        "total_cards": deck_state["total_cards"],
    }

    def compute_quality(state):
        """Quality score: how well we meet role quotas and curve targets."""
        quality = 0.0
        # Role quota satisfaction
        for role, (mn, mx) in blueprint.role_quotas.items():
            target = blueprint.role_target_count(role)
            current = state["role_counts"].get(role, 0)
            if current < target:
                quality -= (target - current) * 2.0  # penalty for missing
            elif current > mx:
                quality -= (current - mx) * 1.0  # penalty for excess
        # Curve match
        total_spells = state["total_spells"]
        if total_spells > 0:
            for mv, target_frac in blueprint.curve_targets.items():
                current_frac = state["curve_counts"].get(mv, 0) / total_spells
                quality -= abs(target_frac - current_frac) * 5.0
        return quality

    best_quality = compute_quality(best_state)

    for _ in range(iterations):
        if len(best_selected) < 2:
            break
        # Pick a random card to remove (non-land, non-commander)
        non_lands = [i for i, c in enumerate(best_selected) if not is_land(c)]
        if not non_lands:
            break
        remove_idx = random.choice(non_lands)
        removed = best_selected[remove_idx]

        # Pick a random candidate to add
        if not candidates:
            break
        add_card = random.choice(candidates)
        add_name = norm(add_card["name"])
        if any(norm(c["name"]) == add_name for c in best_selected):
            continue  # already have it (singleton/4-of)

        # Try swap
        new_selected = list(best_selected)
        new_selected[remove_idx] = dict(add_card, qty_to_play=1)

        # Recompute state quickly
        new_state = {
            "role_counts": defaultdict(int),
            "curve_counts": defaultdict(int),
            "tribe_counts": defaultdict(int),
            "total_spells": 0,
            "total_lands": 0,
            "total_cards": 0,
        }
        for c in new_selected:
            if is_land(c):
                new_state["total_lands"] += c.get("qty_to_play", 1)
            else:
                new_state["total_spells"] += 1
                for role in c.get("functional_roles", []):
                    new_state["role_counts"][role] += 1
                mv = printed_mv(c.get("mana_cost") or "")
                new_state["curve_counts"][mv] += 1
                for tribe in c.get("synergy_features", {}).get("tribes", []):
                    new_state["tribe_counts"][tribe] += 1
            new_state["total_cards"] += c.get("qty_to_play", 1)

        new_quality = compute_quality(new_state)
        if new_quality > best_quality:
            best_selected = new_selected
            best_state = dict(new_state)
            best_state["role_counts"] = dict(new_state["role_counts"])
            best_state["curve_counts"] = dict(new_state["curve_counts"])
            best_state["tribe_counts"] = dict(new_state["tribe_counts"])
            best_quality = new_quality

    return best_selected, best_state


def write_deck_file(
    selected: List[dict],
    blueprint,
    commander_name: Optional[str],
    path: str,
) -> str:
    """Write deck in Arena import format. Returns the file path."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    lines = []
    if blueprint.format == "brawl" and commander_name:
        lines.append("Commander")
        lines.append(f"1 {commander_name}")
        lines.append("")

    lines.append("Deck")
    # Group by name
    grouped: Dict[str, int] = defaultdict(int)
    for c in selected:
        grouped[c["name"]] += c.get("qty_to_play", 1)

    for name in sorted(grouped.keys(), key=norm):
        lines.append(f"{grouped[name]} {name}")

    if blueprint.format == "standard":
        lines.append("")
        lines.append("Sideboard")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"Wrote deck: {path}")
    return path


def run_deck_check(deck_path: str, fmt: str) -> Tuple[bool, str]:
    """Run scripts/deck_check.py on the deck. Returns (ok, output)."""
    check_script = os.path.join(HERE, "deck_check.py")
    result = subprocess.run(
        [sys.executable, check_script, deck_path, "--format", fmt],
        capture_output=True, text=True, cwd=ROOT
    )
    output = result.stdout + result.stderr
    return (result.returncode == 0, output)


def build_deck(
    format_name: str,
    archetype: Optional[str] = None,
    commander: Optional[str] = None,
    max_wildcards: int = 0,
    owned_only: bool = True,
    simulate: bool = False,
    output_path: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """Build a deck end-to-end. Returns (ok, deck_path, rationale)."""

    pool = load_enriched_pool()

    if format_name == "brawl" and not commander:
        return False, "", "Brawl requires --commander"
    if format_name == "standard" and not archetype:
        return False, "", "Standard requires --archetype"

    blueprint = get_blueprint(format_name, archetype or "brawl_commander")

    # Filter candidates
    candidates = filter_candidates(
        pool, blueprint, owned_only, max_wildcards, commander
    )

    if not candidates:
        return False, "", "No candidates found matching constraints"

    # Greedy build
    selected, deck_state = greedy_build(candidates, blueprint, max_wildcards, owned_only, pool)

    # Local-swap optimization
    selected, deck_state = local_swap_optimize(
        selected, deck_state, blueprint, candidates, pool
    )

    # Determine output path
    if not output_path:
        name_part = commander or archetype or "deck"
        safe_name = "".join(c if c.isalnum() or c in "-_" else "-" for c in name_part)
        fmt_prefix = "brawl100-" if format_name == "brawl" else ""
        output_path = os.path.join(DECKS_DIR, f"{fmt_prefix}{safe_name}.txt")

    # Write deck file
    write_deck_file(selected, blueprint, commander, output_path)

    # Validate via deck_check.py
    ok, check_output = run_deck_check(output_path, format_name)

    # Build rationale
    rationale_lines = []
    rationale_lines.append(f"Deck: {os.path.basename(output_path)}")
    rationale_lines.append(f"Format: {format_name} ({blueprint.archetype})")
    rationale_lines.append(f"Blueprint: lands={blueprint.land_target}, "
                           f"spells={blueprint.total_cards() - blueprint.land_target}")
    rationale_lines.append("")

    rationale_lines.append("Role quotas vs. built:")
    for role, (mn, mx) in sorted(blueprint.role_quotas.items()):
        target = blueprint.role_target_count(role)
        actual = deck_state["role_counts"].get(role, 0)
        status = "OK" if mn <= actual <= mx else ("UNDER" if actual < mn else "OVER")
        rationale_lines.append(f"  {role:<20} target={target:>3} actual={actual:>3} [{status}]")

    rationale_lines.append("")
    rationale_lines.append("Curve distribution:")
    total_spells = deck_state["total_spells"]
    for mv in sorted(blueprint.curve_targets.keys()):
        target = blueprint.curve_targets[mv]
        actual_count = deck_state["curve_counts"].get(mv, 0)
        actual_frac = actual_count / max(1, total_spells)
        rationale_lines.append(f"  MV {mv}: target={target:.0%} actual={actual_frac:.0%} "
                               f"({actual_count} cards)")

    rationale_lines.append("")
    rationale_lines.append("Mana base:")
    color_reqs = deck_state.get("color_requirements", {})
    unmet = deck_state.get("unmet_mana", [])
    if unmet:
        rationale_lines.append("  UNMET color requirements:")
        for color, needed, have in unmet:
            rationale_lines.append(f"    {color}: need {needed}, have {have}")
    else:
        rationale_lines.append("  All color requirements met")

    rationale_lines.append("")
    rationale_lines.append("Card selection rationale (Oracle-grounded):")
    grouped: Dict[str, int] = defaultdict(int)
    for c in selected:
        grouped[c["name"]] += c.get("qty_to_play", 1)
    for name in sorted(grouped.keys(), key=norm):
        card = pool.get(name, {})
        roles = card.get("functional_roles", [])
        oracle = card.get("oracle_text", "")
        oracle_short = (oracle[:100] + "...") if len(oracle) > 100 else oracle
        rationale_lines.append(f"  {grouped[name]}x {name}")
        if roles:
            rationale_lines.append(f"      roles: {', '.join(roles)}")
        if oracle_short:
            rationale_lines.append(f"      oracle: {oracle_short}")

    if not ok:
        rationale_lines.append("")
        rationale_lines.append("DECK CHECK FAILED:")
        rationale_lines.append(check_output)

    rationale = "\n".join(rationale_lines)

    # Optional Monte Carlo simulation
    if simulate:
        rationale_lines.append("")
        rationale_lines.append("Monte Carlo goldfish simulation: not yet run.")
        rationale = "\n".join(rationale_lines)

    return ok, output_path, rationale


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--format", choices=("standard", "brawl"), required=True,
                    help="Format to build")
    ap.add_argument("--archetype", choices=("aggro", "midrange", "control", "tempo"),
                    help="Standard archetype (required for standard)")
    ap.add_argument("--commander", help="Brawl commander name (required for brawl)")
    ap.add_argument("--max-wildcards", type=int, default=0,
                    help="Max wildcard budget (0 = pool-only, default)")
    ap.add_argument("--simulate", action="store_true",
                    help="Run Monte Carlo goldfish simulation after building")
    ap.add_argument("--output", help="Output deck file path")
    args = ap.parse_args()

    ok, deck_path, rationale = build_deck(
        format_name=args.format,
        archetype=args.archetype,
        commander=args.commander,
        max_wildcards=args.max_wildcards,
        owned_only=(args.max_wildcards == 0),
        simulate=args.simulate,
        output_path=args.output,
    )

    print("\n" + "=" * 68)
    print(rationale)
    print("=" * 68)

    if ok:
        print("\nRESULT: Deck built and validated successfully")
        print(f"Arena-importable file: {deck_path}")
        sys.exit(0)
    else:
        print("\nRESULT: Deck built but validation failed (see above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
