#!/usr/bin/env python3
"""Unit tests for archetypes.py — M2 acceptance criteria."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from archetypes import (
    get_blueprint, list_blueprints, STANDARD_BLUEPRINTS,
    BRAWL_BLUEPRINT, Blueprint, ROLES,
)


def test_all_roles_covered():
    """Every role in ROLES should be covered by blueprints."""
    for role in ROLES:
        assert role in STANDARD_BLUEPRINTS["aggro"].role_quotas
        assert role in BRAWL_BLUEPRINT.role_quotas


def test_get_blueprint_standard():
    bp = get_blueprint("standard", "aggro")
    assert bp.format == "standard"
    assert bp.archetype == "aggro"
    assert bp.total_cards() == 60


def test_get_blueprint_brawl():
    bp = get_blueprint("brawl", "brawl_commander")
    assert bp.format == "brawl"
    assert bp.total_cards() == 100


def test_get_blueprint_unknown_format():
    try:
        get_blueprint("pioneer", "aggro")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_get_blueprint_unknown_archetype():
    try:
        get_blueprint("standard", "tribal")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_list_blueprints():
    blueprints = list_blueprints()
    assert ("standard", "aggro") in blueprints
    assert ("standard", "control") in blueprints
    assert ("brawl", "brawl_commander") in blueprints


def test_aggressive_blueprint_curve():
    bp = STANDARD_BLUEPRINTS["aggro"]
    # Aggro should have lots of 1-2 drops
    assert bp.curve_targets[1] > 0.15
    assert bp.curve_targets[2] > 0.20
    # Aggro should have few high drops
    assert bp.curve_targets.get(6, 0) < 0.05


def test_control_blueprint_curve():
    bp = STANDARD_BLUEPRINTS["control"]
    # Control should have more 4+ drops
    assert bp.curve_targets[4] >= 0.20
    assert bp.curve_targets[5] >= 0.15


def test_control_has_more_removal_than_aggro():
    aggro = STANDARD_BLUEPRINTS["aggro"]
    control = STANDARD_BLUEPRINTS["control"]
    aggro_removal = aggro.role_target_count("spot_removal")
    control_removal = control.role_target_count("spot_removal")
    assert control_removal > aggro_removal


def test_control_has_more_card_draw_than_aggro():
    aggro = STANDARD_BLUEPRINTS["aggro"]
    control = STANDARD_BLUEPRINTS["control"]
    aggro_draw = aggro.role_target_count("card_draw")
    control_draw = control.role_target_count("card_draw")
    assert control_draw > aggro_draw


def test_brawl_has_high_ramp():
    brawl = BRAWL_BLUEPRINT
    ramp_count = brawl.role_target_count("ramp")
    assert ramp_count >= 6  # Brawl needs lots of ramp


def test_blueprint_role_target_within_bounds():
    for name, bp in STANDARD_BLUEPRINTS.items():
        for role, (mn, mx) in bp.role_quotas.items():
            target = bp.role_target_count(role)
            assert 0 <= target, f"{name}.{role} target {target} < 0"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
