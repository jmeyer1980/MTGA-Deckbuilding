#!/usr/bin/env python3
\"\"\"Unit tests for deck_builder.py — M3 acceptance criteria.

Tests for the filter_candidates function and --max-wildcards flag behavior.
\"\"\"

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from deck_builder import (
    filter_candidates,
    load_enriched_pool,
    norm,
)


def make_card(
    name,
    oracle_text="",
    type_line="",
    color_identity=None,
    mana_cost="",
    qty=1,
    standard="legal",
    brawl="legal",
    competitivebrawl="legal",
):
    """Create a minimal card entry for testing."""
    return {
        "name": name,
        "mana_cost": mana_cost,
        "cmc": 0,
        "type_line": type_line,
        "color_identity": color_identity or [],
        "oracle_text": oracle_text,
        "qty": qty,
        "standard": standard,
        "brawl": brawl,
        "competitivebrawl": competitivebrawl,
    }


def test_filter_candidates_owned_only():
    \"\"\"Test that filter_candidates with owned_only=True only includes cards with qty > 0.\"\"\"
    pool = {
        "Card A": make_card("Card A", qty=2, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card B": make_card("Card B", qty=0, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card C": make_card("Card C", qty=1, type_line="Creature", color_identity=["G"], mana_cost="{G}"),
    }

    blueprint = {
        "roles": [],
        "curve_targets": {},
    }

    # With owned_only=True, only cards with qty > 0 should be included
    candidates = filter_candidates(pool, blueprint, owned_only=True, max_wildcards=0)
    card_names = {c["name"] for c in candidates}
    assert "Card A" in card_names, f\"Expected Card A in candidates, got {card_names}\"
    assert "Card B" not in card_names, f\"Expected Card B NOT in candidates (qty=0), got {card_names}\"
    assert "Card C" in card_names, f\"Expected Card C in candidates, got {card_names}\"


def test_filter_candidates_max_wildcards():
    \"\"\"Test that filter_candidates with max_wildcards > 0 includes all pool cards.\"\"\"
    pool = {
        "Card A": make_card("Card A", qty=2, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card B": make_card("Card B", qty=0, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card C": make_card("Card C", qty=1, type_line="Creature", color_identity=["G"], mana_cost="{G}"),
    }

    blueprint = {
        "roles": [],
        "curve_targets": {},
    }

    # With max_wildcards > 0 and owned_only=False, all cards should be included
    candidates = filter_candidates(pool, blueprint, owned_only=False, max_wildcards=10)
    card_names = {c["name"] for c in candidates}
    assert "Card A" in card_names, f\"Expected Card A in candidates, got {card_names}\"
    assert "Card B" in card_names, f\"Expected Card B in candidates (max_wildcards > 0), got {card_names}\"
    assert "Card C" in card_names, f\"Expected Card C in candidates, got {card_names}\"


def test_filter_candidates_default_owned_only():
    \"\"\"Test default behavior: owned_only=(max_wildcards == 0).\"\"\"
    pool = {
        "Card A": make_card("Card A", qty=2, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card B": make_card("Card B", qty=0, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
    }

    blueprint = {
        "roles": [],
        "curve_targets": {},
    }

    # Default: max_wildcards=0 → owned_only=True
    candidates = filter_candidates(pool, blueprint, owned_only=True, max_wildcards=0)
    card_names = {c["name"] for c in candidates}
    assert "Card A" in card_names
    assert "Card B" not in card_names


def test_load_enriched_pool_fallback():
    \"\"\"Test that load_enriched_pool falls back to pool.json when enriched not available.\"\"\"
    # Create a temporary pool.json
    test_pool = {
        "Test Card": make_card("Test Card", qty=1, type_line="Instant", color_identity=["R"], mana_cost="{R}")
    }

    test_pool_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "test_pool.json")
    with open(test_pool_path, "w", encoding="utf-8") as f:
        json.dump({"pool": test_pool}, f)

    try:
        pool = load_enriched_pool()
        card_names = {name for name in pool.keys()}
        assert "Test Card" in card_names, f\"Expected Test Card in pool, got {card_names}\"
    finally:
        os.remove(test_pool_path)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))