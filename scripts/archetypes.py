#!/usr/bin/env python3
"""Format-specific strategy blueprints with role quotas and mana-curve targets.

Each blueprint defines:
  * format: "standard" (60-card) or "brawl" (100-card)
  * archetype: e.g. "aggro", "midrange", "control", "tempo", "brawl_commander"
  * role_quotas: min/max counts per functional role (ramp, spot_removal, etc.)
  * curve_targets: ideal distribution of mana values 0-7+
  * land_target: preferred land count (adjusted by mana_solver)
  * notes: human-readable strategy summary

Used by scripts/deck_builder.py to score and select cards.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

ROLES = (
    "ramp", "spot_removal", "board_wipe", "card_draw", "counterspell",
    "protection", "token_maker", "lifegain", "graveyard_hate", "threat", "payoff",
)


@dataclass
class Blueprint:
    format: str
    archetype: str
    role_quotas: Dict[str, tuple]  # role -> (min, max)
    curve_targets: Dict[int, float]  # mana_value -> fraction (0-1)
    land_target: int
    commander_identity: Optional[List[str]] = None
    notes: str = ""

    def total_cards(self) -> int:
        return 100 if self.format == "brawl" else 60

    def role_target_count(self, role: str) -> int:
        """Return the target count for a role (midpoint of min/max scaled to deck size)."""
        mn, mx = self.role_quotas.get(role, (0, 0))
        # Scale to deck size: quotas are expressed as fractions of non-land slots
        non_land = self.total_cards() - self.land_target
        target = int((mn + mx) / 2 * non_land / 100)
        return max(0, min(target, non_land))


# ---------------------------------------------------------------------------
# Standard (60-card) archetype blueprints
# ---------------------------------------------------------------------------

STANDARD_BLUEPRINTS = {
    "aggro": Blueprint(
        format="standard",
        archetype="aggro",
        role_quotas={
            "ramp": (0, 5),
            "spot_removal": (4, 8),
            "board_wipe": (0, 2),
            "card_draw": (2, 6),
            "counterspell": (0, 4),
            "protection": (0, 4),
            "token_maker": (0, 4),
            "lifegain": (0, 2),
            "graveyard_hate": (0, 2),
            "threat": (16, 24),
            "payoff": (4, 8),
        },
        curve_targets={1: 0.20, 2: 0.30, 3: 0.25, 4: 0.15, 5: 0.05, 6: 0.03, 7: 0.02},
        land_target=22,
        notes="Fast, creature-based strategy. Curve tops at 4. Wins by T4-T6. Emphasizes early creatures and aggressive mana development.",
    ),
    "midrange": Blueprint(
        format="standard",
        archetype="midrange",
        role_quotas={
            "ramp": (4, 8),
            "spot_removal": (8, 12),
            "board_wipe": (0, 3),
            "card_draw": (4, 8),
            "counterspell": (0, 4),
            "protection": (0, 4),
            "token_maker": (0, 4),
            "lifegain": (0, 2),
            "graveyard_hate": (0, 2),
            "threat": (12, 18),
            "payoff": (4, 8),
        },
        curve_targets={2: 0.15, 3: 0.25, 4: 0.25, 5: 0.20, 6: 0.10, 7: 0.05},
        land_target=25,
        notes="Value-oriented. Strong 3-5 drops, answers early, finishes mid-game. Prioritizes card advantage and board control over tempo.",
    ),
    "control": Blueprint(
        format="standard",
        archetype="control",
        role_quotas={
            "ramp": (2, 6),
            "spot_removal": (8, 12),
            "board_wipe": (3, 6),
            "card_draw": (6, 10),
            "counterspell": (6, 10),
            "protection": (0, 4),
            "token_maker": (0, 2),
            "lifegain": (0, 2),
            "graveyard_hate": (0, 2),
            "threat": (2, 6),
            "payoff": (2, 4),
        },
        curve_targets={1: 0.05, 2: 0.10, 3: 0.15, 4: 0.25, 5: 0.20, 6: 0.15, 7: 0.10},
        land_target=26,
        notes="Answer-heavy. Board wipes + counterspells, finish with few big threats. Prioritizes answering opponent's threats before deploying your own.",
    ),
    "tempo": Blueprint(
        format="standard",
        archetype="tempo",
        role_quotas={
            "ramp": (0, 4),
            "spot_removal": (4, 8),
            "board_wipe": (0, 2),
            "card_draw": (2, 6),
            "counterspell": (4, 8),
            "protection": (2, 6),
            "token_maker": (0, 2),
            "lifegain": (0, 2),
            "graveyard_hate": (0, 2),
            "threat": (10, 16),
            "payoff": (2, 4),
        },
        curve_targets={1: 0.15, 2: 0.25, 3: 0.25, 4: 0.20, 5: 0.10, 6: 0.03, 7: 0.02},
        land_target=22,
        notes="Early threats backed by counterspells and protection. Emphasizes developing a board presence while maintaining mana efficiency for interaction. Curve tops at 4 with cheap spells and protection effects.",
    ),
}


# ---------------------------------------------------------------------------
# Brawl (100-card, Commander-centric) blueprint
# ---------------------------------------------------------------------------

BRAWL_BLUEPRINT = Blueprint(
    format="brawl",
    archetype="brawl_commander",
    role_quotas={
        "ramp": (8, 14),
        "spot_removal": (6, 10),
        "board_wipe": (2, 5),
        "card_draw": (8, 12),
        "counterspell": (2, 6),
        "protection": (2, 6),
        "token_maker": (2, 6),
        "lifegain": (0, 4),
        "graveyard_hate": (2, 4),
        "threat": (10, 16),
        "payoff": (4, 8),
    },
    curve_targets={
        1: 0.05, 2: 0.12, 3: 0.18, 4: 0.20, 5: 0.15, 6: 0.12, 7: 0.08, 8: 0.05, 9: 0.05
    },
    land_target=36,
    notes="100-card singleton. Commander is the anchor. Ramp and card draw are premium.",
)


def get_blueprint(format_name: str, archetype: str) -> Blueprint:
    """Look up a blueprint by format and archetype name."""
    if format_name == "standard":
        if archetype not in STANDARD_BLUEPRINTS:
            raise ValueError(
                f"Unknown Standard archetype: {archetype}. "
                f"Options: {', '.join(sorted(STANDARD_BLUEPRINTS))}"
            )
        return STANDARD_BLUEPRINTS[archetype]
    elif format_name == "brawl":
        return BRAWL_BLUEPRINT
    else:
        raise ValueError(f"Unknown format: {format_name}. Use 'standard' or 'brawl'.")


def list_blueprints() -> List[tuple]:
    """Return list of (format, archetype) tuples for all available blueprints."""
    result = [("standard", k) for k in sorted(STANDARD_BLUEPRINTS)]
    result.append(("brawl", "brawl_commander"))
    return result


if __name__ == "__main__":
    for fmt, arch in list_blueprints():
        bp = get_blueprint(fmt, arch)
        print(f"{fmt:10} {arch:20} lands={bp.land_target} "
              f"threat={bp.role_target_count('threat')} "
              f"removal={bp.role_target_count('spot_removal')} "
              f"draw={bp.role_target_count('card_draw')}")
