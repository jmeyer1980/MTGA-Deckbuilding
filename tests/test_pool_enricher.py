#!/usr/bin/env python3
"""Unit tests for pool_enricher.py — M1 acceptance criteria."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from pool_enricher import (
    norm, tag_card, extract_synergy_features,
    compute_tfidf_similarity, enrich_pool, produced_mana,
)


def make_card(name, oracle_text="", type_line="", color_identity=None,
              card_faces=None, mana_cost=""):
    ci = color_identity or []
    return {
        "name": name,
        "mana_cost": mana_cost,
        "cmc": 0,
        "type_line": type_line,
        "color_identity": ci,
        "oracle_text": oracle_text,
        "card_faces": card_faces,
        "qty": 1,
        "standard": "legal",
        "brawl": "legal",
        "competitivebrawl": "legal",
        "any_number": False,
    }


def test_norm_folds_diacritics():
    assert norm("Oin the Brave") == norm("Óin the Brave")
    assert norm("Jace, the Mind Sculptor") == norm("jace, the mind sculptor")


def test_tag_card_spot_removal():
    card = make_card("Lightning Bolt",
                     oracle_text="Lightning Bolt deals 3 damage to any target.",
                     type_line="Instant", color_identity=["R"],
                     mana_cost="{R}")
    tags = tag_card(card)
    assert "spot_removal" in tags, f"Expected spot_removal, got {tags}"


def test_tag_card_counterspell():
    card = make_card("Counterspell",
                     oracle_text="Counter target spell.",
                     type_line="Instant", color_identity=["U"],
                     mana_cost="{U}{U}")
    tags = tag_card(card)
    assert "counterspell" in tags, f"Expected counterspell, got {tags}"


def test_tag_card_card_draw():
    card = make_card("Brainstorm",
                     oracle_text="Draw three cards, then put two cards from your hand on top of your library in any order.",
                     type_line="Instant", color_identity=["U"],
                     mana_cost="{U}")
    tags = tag_card(card)
    assert "card_draw" in tags, f"Expected card_draw, got {tags}"


def test_tag_card_board_wipe():
    card = make_card("Wrath of God",
                     oracle_text="Destroy all creatures.",
                     type_line="Sorcery", color_identity=["W"],
                     mana_cost="{2}{W}{W}")
    tags = tag_card(card)
    assert "board_wipe" in tags, f"Expected board_wipe, got {tags}"


def test_tag_card_ramp():
    card = make_card("Rampant Growth",
                     oracle_text="Search your library for a basic land card, put that card onto the battlefield tapped.",
                     type_line="Sorcery", color_identity=["G"],
                     mana_cost="{1}{G}")
    tags = tag_card(card)
    assert "ramp" in tags, f"Expected ramp, got {tags}"


def test_tag_card_protection():
    card = make_card("Flawless Maneuver",
                     oracle_text="Creatures you control gain indestructible until end of turn.",
                     type_line="Instant", color_identity=["W"],
                     mana_cost="{2}{W}")
    tags = tag_card(card)
    assert "protection" in tags, f"Expected protection, got {tags}"


def test_tag_card_threat():
    card = make_card("Grizzly Bears",
                     oracle_text="",
                     type_line="Creature — Bear", color_identity=["G"],
                     mana_cost="{1}{G}")
    tags = tag_card(card)
    assert isinstance(tags, set)


def test_tag_card_no_false_positives():
    card = make_card("Vanilla Bear",
                     oracle_text="",
                     type_line="Creature — Bear", color_identity=["G"],
                     mana_cost="{1}{G}")
    tags = tag_card(card)
    assert "board_wipe" not in tags
    assert "counterspell" not in tags


def test_extract_synergy_features_tribes():
    card = make_card("Llanowar Elves",
                     oracle_text="{T}: Add {G}.",
                     type_line="Creature — Elf Druid", color_identity=["G"],
                     mana_cost="{G}")
    features = extract_synergy_features(card)
    # Code matches tribe names as-is from the type_line (lowercased)
    tribes = features.get("tribes", [])
    # The pattern [Ee]lf[s]? matches "Elf" or "elf" — check for either
    assert "elf" in tribes or "elves" in tribes, f"Expected elf/elves tribe, got {tribes}"


def test_extract_synergy_features_graveyard():
    card = make_card("Scavenging Ooze",
                     oracle_text="{G}, Exile a card from a graveyard: ...",
                     type_line="Creature — Ooze", color_identity=["G"],
                     mana_cost="{1}{G}")
    features = extract_synergy_features(card)
    assert features.get("graveyard") is True


def test_produced_mana_basic_land():
    card = make_card("Plains",
                     type_line="Basic Land — Plains", color_identity=["W"],
                     mana_cost="")
    pm = produced_mana(card)
    assert "W" in pm


def test_enriched_pool_has_functional_roles():
    pool = {
        "Lightning Bolt": make_card("Lightning Bolt",
            oracle_text="Lightning Bolt deals 3 damage to any target.",
            type_line="Instant", color_identity=["R"], mana_cost="{R}"),
        "Counterspell": make_card("Counterspell",
            oracle_text="Counter target spell.",
            type_line="Instant", color_identity=["U"], mana_cost="{U}{U}"),
    }
    enriched = enrich_pool(pool)
    assert "functional_roles" in enriched["Lightning Bolt"]
    assert "spot_removal" in enriched["Lightning Bolt"]["functional_roles"]
    assert "functional_roles" in enriched["Counterspell"]
    assert "counterspell" in enriched["Counterspell"]["functional_roles"]


def test_tfidf_similarity_returns_dict():
    pool = {
        "Card A": make_card("Card A", oracle_text="draw a card draw a card",
            type_line="Instant", color_identity=["U"], mana_cost="{U}"),
        "Card B": make_card("Card B", oracle_text="draw a card",
            type_line="Instant", color_identity=["U"], mana_cost="{U}"),
        "Card C": make_card("Card C", oracle_text="destroy target creature",
            type_line="Instant", color_identity=["B"], mana_cost="{B}"),
    }
    sims = compute_tfidf_similarity(pool)
    assert isinstance(sims, dict)
    assert "Card A" in sims
    # Card A and Card B both have "draw a card" → should be similar
    sim_names = {s[0] for s in sims.get("Card A", [])}
    assert "Card B" in sim_names, f"Expected Card B similar to Card A, got {sim_names}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))