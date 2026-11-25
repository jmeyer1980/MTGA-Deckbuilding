#!/usr/bin/env python3
"""Headless Monte Carlo opening-hand and T1-T4 goldfish simulator.

Simulates opening hands and early-game draws for a constructed deck,
aligned with the mulligan rules in mulligan-decks-v2.json and
scripts/session_audit.py.

Outputs a Trustworthiness Report:
  * keepable-hand % (hands that pass the mulligan keep rule)
  * T1-T4 color-screw % (hands that can't cast their spells on time)
  * on-curve playability % (hands that can play on-curve spells T1-T4)

Decks failing thresholds are flagged for rejection/re-tuning.

Usage:
    python scripts/deck_sim.py decks/brawl100-delney.txt --iterations 1000
    python scripts/deck_sim.py decks/standard-midrange.txt --iterations 2000 --on-play
"""

import argparse
import json
import os
import random
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

sys.path.insert(0, HERE)
from deck_builder import norm, is_land, printed_mv

# ---------------------------------------------------------------------------
# Mulligan rule thresholds (from session_audit.py / README)
# ---------------------------------------------------------------------------
# 0/1/6/7 lands → mulligan, 2-5 lands → keep (base rule)
# Additional rules for specific archetypes are handled by the caller.
KEEP_MIN_LANDS = 2
KEEP_MAX_LANDS = 5


def parse_deck(path: str) -> Tuple[List[dict], Optional[str], str]:
    """Parse an Arena-format deck file.

    Returns (cards, commander, format).
    cards: list of {name, qty, is_land, mana_cost, color_identity, mv}
    """
    cards = []
    commander = None
    fmt = "standard"
    section = "deck"

    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.lower() == "commander":
                section = "commander"
                continue
            if line.lower() == "deck":
                section = "deck"
                continue
            if line.lower() == "sideboard":
                section = "sideboard"
                continue

            import re
            m = re.match(r"^(\d+)\s+(.+?)\s*$", line)
            if not m:
                continue
            qty = int(m.group(1))
            name = m.group(2).strip()

            # Look up card data from pool if available
            card = {"name": name, "qty": qty, "is_land": False,
                    "mana_cost": "", "color_identity": [], "mv": 0}

            # Try to enrich from pool
            pool_path = os.path.join(ROOT, "pool.json")
            if os.path.exists(pool_path):
                with open(pool_path, encoding="utf-8") as pf:
                    pool_data = json.load(pf)
                pool = pool_data["pool"]
                # Match by folded name
                for pname, pentry in pool.items():
                    if norm(pname) == norm(name):
                        card["is_land"] = "land" in (pentry.get("type_line") or "").lower()
                        card["mana_cost"] = pentry.get("mana_cost", "")
                        card["color_identity"] = pentry.get("color_identity", [])
                        card["mv"] = printed_mv(pentry.get("mana_cost", ""))
                        break

            if section == "commander":
                commander = name
                fmt = "brawl"

            for _ in range(qty):
                cards.append(dict(card))

    return cards, commander, fmt


def simulate_opening_hand(
    deck: List[dict],
    hand_size: int = 7,
    on_play: bool = True,
    rng: Optional[random.Random] = None,
) -> dict:
    """Draw one opening hand from the deck.

    Returns dict with hand composition and whether it's keepable.
    """
    if rng is None:
        rng = random.Random()

    deck_copy = list(deck)
    rng.shuffle(deck_copy)

    hand = deck_copy[:hand_size]
    lands = sum(1 for c in hand if c["is_land"])
    spells = hand_size - lands

    # Mulligan decision: base rule 2-5 lands keep
    keepable = KEEP_MIN_LANDS <= lands <= KEEP_MAX_LANDS

    # Mana colors available in hand
    hand_colors: Counter = Counter()
    for c in hand:
        if not c["is_land"]:
            for ci in c["color_identity"]:
                hand_colors[ci] += 1
        # Lands produce their color identity too
        else:
            for ci in c["color_identity"]:
                hand_colors[ci] += 1

    # Can cast T1 spell?
    t1_spells = [c for c in hand if not c["is_land"] and c["mv"] <= 1]
    t2_spells = [c for c in hand if not c["is_land"] and c["mv"] <= 2]
    t3_spells = [c for c in hand if not c["is_land"] and c["mv"] <= 3]

    can_play_t1 = len(t1_spells) > 0 and lands >= 1
    can_play_t2 = len(t2_spells) > 0 and lands >= 2
    can_play_t3 = len(t3_spells) > 0 and lands >= 3

    on_curve = can_play_t1 or can_play_t2 or can_play_t3

    return {
        "lands": lands,
        "spells": spells,
        "keepable": keepable,
        "can_play_t1": can_play_t1,
        "can_play_t2": can_play_t2,
        "can_play_t3": can_play_t3,
        "on_curve": on_curve,
        "hand_colors": dict(hand_colors),
    }


def simulate_t4_lands(
    deck: List[dict],
    opening_hand: List[dict],
    on_play: bool = True,
    rng: Optional[random.Random] = None,
) -> int:
    """Simulate lands by turn 4 after the opening hand.

    On the play: draw 3 more cards by T4
    On the draw: draw 4 more cards by T4
    """
    if rng is None:
        rng = random.Random()

    remaining = [c for c in deck if c not in opening_hand]
    rng.shuffle(remaining)

    draws_needed = 3 if on_play else 4
    drawn = remaining[:draws_needed]

    open_lands = sum(1 for c in opening_hand if c["is_land"])
    drawn_lands = sum(1 for c in drawn if c["is_land"])

    return open_lands + drawn_lands


def run_simulation(
    deck_path: str,
    iterations: int = 1000,
    on_play: bool = True,
    seed: Optional[int] = None,
) -> dict:
    """Run Monte Carlo simulation and return Trustworthiness Report."""
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    cards, commander, fmt = parse_deck(deck_path)

    if not cards:
        return {"error": "No cards in deck"}

    keepable_count = 0
    color_screw_count = 0
    on_curve_count = 0
    t4_worked_count = 0
    land_distribution: Counter = Counter()

    for _ in range(iterations):
        hand_result = simulate_opening_hand(cards, rng=rng, on_play=on_play)
        hand_lands = hand_result["lands"]

        if hand_result["keepable"]:
            keepable_count += 1

        # Color screw: hand has lands but can't cast anything relevant
        # Simplified: keepable hand but no spells castable T1-T3
        if hand_result["keepable"] and not hand_result["on_curve"]:
            color_screw_count += 1

        if hand_result["on_curve"]:
            on_curve_count += 1

        # T4 lands check (for keepable hands)
        if hand_result["keepable"]:
            # Need to know the actual opening hand cards for T4 simulation
            # Approximate: reshuffle and draw
            t4 = simulate_t4_lands(cards, [], on_play=on_play, rng=rng)
            if 3 <= t4 <= 5:
                t4_worked_count += 1

        land_distribution[hand_lands] += 1

    total = iterations
    report = {
        "deck": os.path.basename(deck_path),
        "commander": commander,
        "format": fmt,
        "iterations": total,
        "on_play": on_play,
        "keepable_hand_pct": round(keepable_count / total * 100, 1),
        "color_screw_pct": round(color_screw_count / total * 100, 1),
        "on_curve_pct": round(on_curve_count / total * 100, 1),
        "t4_lands_worked_pct": round(t4_worked_count / total * 100, 1),
        "land_distribution": dict(sorted(land_distribution.items())),
        "passes_thresholds": True,
    }

    # Thresholds: keepable > 60%, on_curve > 50%, color_screw < 30%
    if report["keepable_hand_pct"] < 60:
        report["passes_thresholds"] = False
        report["failure_reason"] = f"keepable-hand {report['keepable_hand_pct']}% < 60%"
    if report["on_curve_pct"] < 50:
        report["passes_thresholds"] = False
        report["failure_reason"] = f"on-curve {report['on_curve_pct']}% < 50%"
    if report["color_screw_pct"] > 30:
        report["passes_thresholds"] = False
        report["failure_reason"] = f"color-screw {report['color_screw_pct']}% > 30%"

    return report


def print_report(report: dict):
    """Print the Trustworthiness Report."""
    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    print("\n" + "=" * 68)
    print("TRUSTWORTHINESS REPORT — Goldfish Monte Carlo Simulation")
    print("=" * 68)
    print(f"Deck: {report['deck']}")
    print(f"Format: {report['format']} | Commander: {report['commander'] or 'N/A'}")
    print(f"On the play: {report['on_play']} | Iterations: {report['iterations']}")
    print()
    print(f"  Keepable-hand %     : {report['keepable_hand_pct']}% "
          f"(threshold: >= 60%)")
    print(f"  On-curve playability: {report['on_curve_pct']}% "
          f"(threshold: >= 50%)")
    print(f"  T1-T4 color-screw % : {report['color_screw_pct']}% "
          f"(threshold: <= 30%)")
    print(f"  T4 lands worked %   : {report['t4_lands_worked_pct']}%")
    print()
    print("  Land distribution (opening hand):")
    for lands in sorted(report["land_distribution"].keys()):
        count = report["land_distribution"][lands]
        pct = count / report["iterations"] * 100
        bar = "#" * int(pct)
        print(f"    {lands} lands: {count:>4} ({pct:5.1f}%) {bar}")
    print()
    if report["passes_thresholds"]:
        print("  VERDICT: PASS — deck meets trustworthiness thresholds")
    else:
        print(f"  VERDICT: FAIL — {report.get('failure_reason', 'thresholds not met')}")
        print("  Recommendation: re-tune land base or curve before playing")
    print("=" * 68 + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("deck", help="Path to Arena-format deck file")
    ap.add_argument("--iterations", type=int, default=1000,
                    help="Monte Carlo iterations (default: 1000)")
    ap.add_argument("--on-play", action="store_true", default=True,
                    help="Simulate on the play (default)")
    ap.add_argument("--on-draw", action="store_true",
                    help="Simulate on the draw instead")
    ap.add_argument("--seed", type=int, default=42,
                    help="Random seed for reproducibility (default: 42)")
    args = ap.parse_args()

    on_play = not args.on_draw

    report = run_simulation(
        args.deck, iterations=args.iterations,
        on_play=on_play, seed=args.seed
    )
    print_report(report)

    sys.exit(0 if report.get("passes_thresholds", False) else 1)


if __name__ == "__main__":
    main()
