#!/usr/bin/env python3
"""Unit tests for mana_solver.py — M2 acceptance criteria."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from mana_solver import (
    hypergeometric_ge, sources_needed, color_source_requirements,
    solve_land_base, validate_mana_base,
)


def test_hypergeometric_basic():
    # P(drawing >=1 success in 7 draws from 60 with 24 successes) should be high
    p = hypergeometric_ge(60, 24, 7, 1)
    assert p > 0.95, f"Expected >0.95, got {p}"

    # P(drawing >=7 successes in 7 draws from 60 with 24 successes) should be tiny
    p = hypergeometric_ge(60, 24, 7, 7)
    assert p < 0.01, f"Expected <0.01, got {p}"

    # P(drawing >=0) = 1
    assert hypergeometric_ge(60, 24, 7, 0) == 1.0


def test_sources_needed_t1_pip():
    sources = sources_needed(1, 1, 60)
    assert sources >= 10, f"Expected >=10, got {sources}"
    assert sources <= 20, f"Expected <=20, got {sources}"


def test_sources_needed_t4_pip():
    sources = sources_needed(4, 3, 60)
    assert sources >= 20, f"Expected >=20, got {sources}"


def test_sources_needed_brawl_scaled():
    brawl_sources = sources_needed(1, 1, 100)
    std_sources = sources_needed(1, 1, 60)
    # Brawl needs more sources due to larger deck
    assert brawl_sources >= std_sources


def test_color_source_requirements_empty():
    cards = []
    reqs = color_source_requirements(cards, 60)
    assert reqs == {}


def test_color_source_requirements_mono_red():
    cards = [
        {"name": "Lightning Bolt", "color_identity": ["R"],
         "mana_cost": "{R}", "cmc": 1, "qty": 4},
        {"name": "Lightning Strike", "color_identity": ["R"],
         "mana_cost": "{1}{R}", "cmc": 2, "qty": 4},
    ]
    reqs = color_source_requirements(cards, 60)
    assert "R" in reqs
    assert reqs["R"] >= 12  # T1 1-pip needs ~12 sources


def test_solve_land_base():
    color_reqs = {"R": 14}
    owned_lands = [
        {"name": "Mountain", "color_identity": ["R"],
         "type_line": "Basic Land — Mountain", "qty": 10},
        {"name": "Plains", "color_identity": ["W"],
         "type_line": "Basic Land — Plains", "qty": 10},
    ]
    selected, unmet = solve_land_base(color_reqs, owned_lands, 60, 24)
    assert len(selected) > 0
    total_lands = sum(l.get("qty_to_play", l.get("qty", 0)) for l in selected)
    assert total_lands <= 24


def test_validate_mana_base():
    lands = [
        {"name": "Mountain", "color_identity": ["R"],
         "qty_to_play": 20},
        {"name": "Plains", "color_identity": ["W"],
         "qty_to_play": 4},
    ]
    reqs = {"R": 14}
    ok, issues = validate_mana_base(lands, reqs)
    assert ok is True
    assert issues == []

    # Under-sourced
    reqs2 = {"R": 30}
    ok2, issues2 = validate_mana_base(lands, reqs2)
    assert ok2 is False
    assert len(issues2) > 0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
