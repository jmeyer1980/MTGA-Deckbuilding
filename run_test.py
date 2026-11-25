#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from deck_builder import filter_candidates, load_enriched_pool, norm

def make_card(name, qty=1, type_line="", color_identity=None, mana_cost=""):
    return {
        "name": name,
        "mana_cost": mana_cost,
        "cmc": 0,
        "type_line": type_line,
        "color_identity": color_identity or [],
        "oracle_text": "",
        "qty": qty,
    }

def test_filter_candidates_owned_only():
    pool = {
        "Card A": make_card("Card A", qty=2, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card B": make_card("Card B", qty=0, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card C": make_card("Card C", qty=1, type_line="Creature", color_identity=["G"], mana_cost="{G}"),
    }
    blueprint = {"roles": [], "curve_targets": {}}
    
    candidates = filter_candidates(pool, blueprint, owned_only=True, max_wildcards=0)
    card_names = {c["name"] for c in candidates}
    
    print(f"Owned only test - candidates: {card_names}")
    assert "Card A" in card_names, f"Expected Card A in candidates, got {card_names}"
    assert "Card B" not in card_names, f"Expected Card B NOT in candidates (qty=0), got {card_names}"
    assert "Card C" in card_names, f"Expected Card C in candidates, got {card_names}"
    print("✓ Owned only test passed!")

def test_filter_candidates_max_wildcards():
    pool = {
        "Card A": make_card("Card A", qty=2, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card B": make_card("Card B", qty=0, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card C": make_card("Card C", qty=1, type_line="Creature", color_identity=["G"], mana_cost="{G}"),
    }
    blueprint = {"roles": [], "curve_targets": {}}
    
    candidates = filter_candidates(pool, blueprint, owned_only=False, max_wildcards=10)
    card_names = {c["name"] for c in candidates}
    
    print(f"Max wildcards test - candidates: {card_names}")
    assert "Card A" in card_names, f"Expected Card A in candidates, got {card_names}"
    assert "Card B" in card_names, f"Expected Card B in candidates (max_wildcards > 0), got {card_names}"
    assert "Card C" in card_names, f"Expected Card C in candidates, got {card_names}"
    print("✓ Max wildcards test passed!")

def test_filter_candidates_default():
    pool = {
        "Card A": make_card("Card A", qty=2, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Card B": make_card("Card B", qty=0, type_line="Instant", color_identity=["R"], mana_cost="{R}"),
    }
    blueprint = {"roles": [], "curve_targets": {}}
    
    # Default: max_wildcards=0 → owned_only=True
    candidates = filter_candidates(pool, blueprint, owned_only=True, max_wildcards=0)
    card_names = {c["name"] for c in candidates}
    
    print(f"Default test - candidates: {card_names}")
    assert "Card A" in card_names
    assert "Card B" not in card_names
    print("✓ Default test passed!")

if __name__ == "__main__":
    test_filter_candidates_owned_only()
    test_filter_candidates_max_wildcards()
    test_filter_candidates_default()
    print("\nAll tests passed!")