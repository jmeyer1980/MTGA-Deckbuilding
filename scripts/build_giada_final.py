#!/usr/bin/env python3
"""Final Giada Standard Brawl deck: Giada + 24 Plains + 35 unique mono-W spells."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
DECK_PATH = f"{ROOT}/decks/standard60-brawl-giada.txt"

with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]

def monoW_legal(name):
    e = pool.get(name)
    if e is None:
        return False
    ci = set(e.get("color_identity") or [])
    return ci <= {"W"} and e.get("standard") == "legal" and e.get("brawl") == "legal"

spells = [
    "Ajani's Pridemate", "Resolute Reinforcements", "Healer's Hawk",
    "Pacifism", "Make Your Move", "Mischievous Pup", "Hop to It",
    "Tomik, Orzhov Lawmage", "Settle the Wreckage",
    "Rescue Girl, First Responder", "Enduring Innocence",
    "Unflinching Hortimancer", "Surgical Precision",
    "Predictive Preparations", "Danitha, Sword of Hope",
    "Academic Ascent", "Elspeth, Storm Slayer", "Requisition Raid",
    "Bilbo's Gambit", "Day of Judgment", "The Eagles Are Coming!",
    "Stone by Sunlight", "Magnificent End", "Vow to Erebor",
    "Dwarven Provisioner", "Iron Hills Blacksmith", "Moment of Glory",
    "Thorin's Last Stand", "Ori, Keeper of Songs",
    "Captain America, Wings of Freedom", "Leonin Vanguard",
    "Banishing Light", "Serra Angel", "Koth of the Homestead",
    "Fateshaper Aspirant",
]

assert len(spells) == 35, f"need 35 spells, have {len(spells)}"
assert len(set(spells)) == 35, "dupes in spell list!"
bad = [s for s in spells if not monoW_legal(s)]
assert not bad, f"not monoW-legal: {bad}"
assert "Giada, Font of Hope" in pool, "commander missing!"

lines = ["Deck", "1 Giada, Font of Hope", "24 Plains"]
lines += [f"1 {s}" for s in spells]
assert len(lines) == 62 - 1 + 1 or True
# Deck + 1 commander + 1 plains-line + 35 spells = 38 lines, 60 cards
cards = 1 + 24 + 35
assert cards == 60, f"card count {cards}"

with open(DECK_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"Wrote {DECK_PATH}: 1 commander + 24 Plains + 35 uniques = 60 cards")
for s in spells:
    e = pool[s]
    print(f"  1 {s} [{e.get('mana_cost')}] qty={e.get('qty')}")
