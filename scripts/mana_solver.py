#!/usr/bin/env python3
"""Hypergeometric color-source mana-base solver (Frank Karsten thresholds).

Calculates the minimum number of colored mana sources needed to cast spells
on curve (T1-T4) using the hypergeometric distribution. Constructs an optimal
land base from owned duals/fetches/utility lands + basics.

Frank Karsten's pip thresholds (approximate, for 60-card decks):
  - T1 1-drop (1 colored pip): ~12 sources for 90%+ consistency
  - T2 2-drop (2 colored pips): ~14-16 sources
  - T3 3-drop (3 colored pips): ~18-20 sources
  - T4 4-drop (4 colored pips): ~22+ sources

For Brawl (100-card), thresholds are scaled by deck size ratio (100/60 ≈ 1.67).
"""

import json
import os
import sys
from math import comb
from typing import Dict, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------------------
# Hypergeometric probability: P(drawing >= k successes in n draws from N with K successes)
# ---------------------------------------------------------------------------

def hypergeometric_ge(N: int, K: int, n: int, k: int) -> float:
    """P(X >= k) where X ~ Hypergeometric(N, K, n)."""
    if k <= 0:
        return 1.0
    if K < k or n < k:
        return 0.0
    total = comb(N, n)
    if total == 0:
        return 0.0
    prob = 0.0
    for x in range(k, min(K, n) + 1):
        prob += comb(K, x) * comb(N - K, n - x) / total
    return prob


# ---------------------------------------------------------------------------
# Frank Karsten color-source thresholds
# Keys: (turn, num_pips) -> min_sources_for_90_percent
# Values are for 60-card decks; scaled for 100-card.
# ---------------------------------------------------------------------------

KARSTEN_THRESHOLDS_60: Dict[Tuple[int, int], int] = {
    # (turn_on_play, pips) -> sources_needed
    (1, 1): 12,
    (1, 2): 18,   # basically impossible T1 with 2 pips in 60
    (2, 1): 14,
    (2, 2): 16,
    (3, 1): 16,
    (3, 2): 18,
    (3, 3): 24,
    (4, 1): 18,
    (4, 2): 20,
    (4, 3): 22,
    (4, 4): 26,
}

# For Brawl (100-card), scale by ~1.67 but cap at reasonable numbers
BRAWL_SCALING = 100 / 60.0


def sources_needed(turn: int, pips: int, deck_size: int = 60) -> int:
    """Minimum colored sources needed to cast a spell with `pips` colored pips
    on `turn` (on the play) with >= 90% probability.

    Uses hypergeometric calculation rather than lookup table for accuracy.
    """
    # Try increasing source counts until we hit 90%+
    # On the play, by turn T you've seen T cards (opening hand 7 + T-1 draws)
    # Actually: T1 play = 7 cards, T2 play = 8 cards, T3 = 9, T4 = 10
    cards_seen = 6 + turn  # 7 opening + (turn-1) draws = turn+6

    for sources in range(pips, deck_size + 1):
        p = hypergeometric_ge(deck_size, sources, cards_seen, pips)
        if p >= 0.90:
            return sources
    return deck_size  # fallback


def color_source_requirements(
    deck_cards: List[dict], deck_size: int = 60
) -> Dict[str, int]:
    """Given a list of cards (with color_identity and mana_cost), compute
    the minimum colored sources needed per color for T1-T4 castability.

    Returns dict mapping color -> min sources needed.
    """
    # Find the most demanding card per color per turn
    # For each color, track max pips needed at each turn
    color_max_pips: Dict[str, Dict[int, int]] = {
        "W": {}, "U": {}, "B": {}, "R": {}, "G": {}
    }

    for card in deck_cards:
        ci = set(card.get("color_identity", []) or [])
        mana_cost = card.get("mana_cost") or ""
        mv = card.get("cmc", 0) or 0

        if not mana_cost or mv == 0:
            continue  # lands or free spells

        # Count colored pips per color in mana cost
        import re
        for color in "WUBRG":
            if color not in ci:
                continue
            # Count pips of this color in mana cost
            pip_count = len(re.findall(r"\{" + color + r"\}", mana_cost))
            if pip_count == 0:
                continue
            # Earliest turn this can be cast (approx = mv for non-X)
            turn = max(1, min(4, int(mv)))
            existing = color_max_pips[color].get(turn, 0)
            color_max_pips[color][turn] = max(existing, pip_count)

    # For each color, find max sources needed across all turns
    requirements: Dict[str, int] = {}
    for color, turn_pips in color_max_pips.items():
        if not turn_pips:
            continue
        max_sources = 0
        for turn, pips in turn_pips.items():
            needed = sources_needed(turn, pips, deck_size)
            max_sources = max(max_sources, needed)
        requirements[color] = max_sources

    return requirements


def solve_land_base(
    color_requirements: Dict[str, int],
    owned_lands: List[dict],
    deck_size: int = 60,
    target_lands: Optional[int] = None,
) -> Tuple[List[dict], List[dict]]:
    """Construct optimal land base from owned lands.

    Args:
        color_requirements: color -> min sources needed
        owned_lands: list of land card dicts from pool (qty > 0)
        deck_size: 60 for Standard, 100 for Brawl
        target_lands: desired total land count (defaults by format)

    Returns:
        (selected_lands, unmet_requirements)
        selected_lands: list of land dicts with 'qty' to include
        unmet_requirements: list of (color, needed, have) for colors short
    """
    if target_lands is None:
        target_lands = 24 if deck_size == 60 else 36

    # Sort owned lands: multicolor duals first (cover multiple requirements),
    # then fetch/utility, then basics
    def land_score(land):
        ci = set(land.get("color_identity", []) or [])
        typ = (land.get("type_line") or "").lower()
        score = 0
        # Prefer lands that cover multiple needed colors
        needed_colors = set(color_requirements.keys())
        score += len(ci & needed_colors) * 10
        # Basic lands are reliable but only one color
        if "basic" in typ:
            score += 1
        # Non-basic that enters tapped is less ideal
        if "enters the battlefield tapped" in (land.get("oracle_text") or "").lower():
            score -= 2
        # Prefer higher qty owned
        score += land.get("qty", 0) * 0.1
        return score

    sorted_lands = sorted(owned_lands, key=land_score, reverse=True)

    selected: List[dict] = []
    color_sources: Dict[str, int] = {c: 0 for c in "WUBRG"}
    total_lands = 0

    # Greedy: pick lands that best cover unmet color requirements
    for land in sorted_lands:
        if total_lands >= target_lands:
            break
        ci = set(land.get("color_identity", []) or [])
        qty = min(land.get("qty", 0), target_lands - total_lands)
        if qty <= 0:
            continue

        # Check if this land helps any unmet color
        helpful = bool(ci & set(color_requirements.keys())) or "basic" in (land.get("type_line") or "").lower()
        if not helpful and total_lands > target_lands * 0.5:
            continue  # skip non-helpful lands once half the base is set

        take = qty
        selected.append({**land, "qty_to_play": take})
        for c in ci:
            if c in color_sources:
                color_sources[c] += take
        total_lands += take

    # Fill remaining slots with basics for colors still short
    for color, needed in sorted(color_requirements.items(), key=lambda x: -x[1]):
        have = color_sources.get(color, 0)
        if have < needed and total_lands < target_lands:
            shortfall = needed - have
            slots_left = target_lands - total_lands
            take = min(shortfall, slots_left)
            # Look for owned basic
            basic_name = {"W": "Plains", "U": "Island", "B": "Swamp",
                          "R": "Mountain", "G": "Forest"}[color]
            selected.append({
                "name": basic_name,
                "color_identity": [color],
                "type_line": f"Basic Land — {basic_name}",
                "qty_to_play": take,
            })
            color_sources[color] += take
            total_lands += take

    # Compute unmet requirements
    unmet = []
    for color, needed in color_requirements.items():
        have = color_sources.get(color, 0)
        if have < needed:
            unmet.append((color, needed, have))

    return selected, unmet


def validate_mana_base(
    selected_lands: List[dict],
    color_requirements: Dict[str, int],
) -> Tuple[bool, List[str]]:
    """Check if selected lands meet color requirements.

    Returns (all_met, list_of_issues).
    """
    color_sources: Dict[str, int] = {c: 0 for c in "WUBRG"}
    for land in selected_lands:
        qty = land.get("qty_to_play", land.get("qty", 0))
        for c in land.get("color_identity", []) or []:
            if c in color_sources:
                color_sources[c] += qty

    issues = []
    for color, needed in color_requirements.items():
        have = color_sources.get(color, 0)
        if have < needed:
            issues.append(f"{color}: need {needed} sources, have {have}")

    return (len(issues) == 0, issues)


if __name__ == "__main__":
    # Quick self-test
    print("Karsten T1 1-pip sources (60-card):", sources_needed(1, 1, 60))
    print("Karsten T2 2-pip sources (60-card):", sources_needed(2, 2, 60))
    print("Karsten T4 3-pip sources (60-card):", sources_needed(4, 3, 60))
    print("Karsten T1 1-pip sources (100-card):", sources_needed(1, 1, 100))
