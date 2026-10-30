#!/usr/bin/env python3
"""Check basics + build final Giada deck from pool-verified mono-W cards."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# 1. Check basics
print("=== Basics check ===")
for b in ["Plains", "Island", "Swamp", "Mountain", "Forest", "Wastes",
          "Snow-Covered Plains", "Snow-Covered Island", "Snow-Covered Swamp",
          "Snow-Covered Mountain", "Snow-Covered Forest"]:
    if b in pool:
        e = pool[b]
        print(f"  {b}: qty={e.get('qty',0)} std={e.get('standard')} brawl={e.get('brawl')} ci={e.get('color_identity')}")
    else:
        print(f"  {b}: NOT IN POOL")

# 2. Build deck: Giada + 59 unique mono-W legal cards
print("\n=== Building deck ===")

def monoW_legal(name, entry):
    ci = set(entry.get("color_identity") or [])
    return ci <= {"W"} and entry.get("standard") == "legal" and entry.get("brawl") == "legal"

# Confirmed in-pool candidates by category (spot-checked above)
lands_pref = [
    "Plains", "Wastes", "Evolving Wilds", "Terramorphic Expanse",
    "Fabled Passage", "Cavern of Souls", "Secluded Courtyard",
    "Lupinflower Village", "Hidden Courtyard", "Abandoned Air Temple",
    "Dalkovan Encampment", "Room of Refuge", "Elven Passage",
    "Conduit Pylons", "Hobbit Hole", "Crystal Grotto", "Escape Tunnel",
    "Surveillance Room", "Valgavoth's Lair", "Starting Town",
    "Skycoach Waypoint", "Edgewall Inn", "Scene of the Crime",
    "Castle Doom", "Demolition Field", "Rogue's Passage",
    "Three Tree City", "Captivating Cave", "Echoing Deeps",
    "Fountainport", "Hidden Grotto", "Uncharted Haven",
    "Soulstone Sanctuary", "Command Bridge", "Multiversal Passage",
    "Vibrant Cityscape",
]
spells_creatures = [
    "Giada, Font of Hope",
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
    "Fateshaper Aspirant", "Way of the Healer", "Prophesied End",
    "Campus Crier", "Graft Surgeon", "Saheeli, Consul of Oversight",
    "Ajani, Caller of the Pride", "Ajani Resolute", "Teferi's Protection",
    "Rest in Peace", "Monastery Swiftspear", "Moment of Triumph",
    "Political Triumph", "Koth of the Homestead", "Wayfarer",
    "Bofur, Reliable Guardian // Concerted Care",
    "An Unexpected Party // At the Door",
    "Velvetwing Butterflies // Gaze in Wonder",
    "Ojer Taq, Deepest Foundation // Temple of Civilization",
]

deck = []
seen = set()
for name in ["Giada, Font of Hope"] + lands_pref + spells_creatures:
    if name in seen:
        continue
    e = pool.get(name)
    if e is None:
        print(f"  SKIP (not in pool): {name}")
        continue
    if name != "Giada, Font of Hope" and not monoW_legal(name, e):
        print(f"  SKIP (not monoW-legal): {name} ci={e.get('color_identity')} std={e.get('standard')} brawl={e.get('brawl')}")
        continue
    seen.add(name)
    deck.append((name, e))

print(f"\nDeck size: {len(deck)}")
names = [d[0] for d in deck]
assert len(names) == len(set(names)), "dupes!"

# Report how many more needed
need = 60 - len(deck)
print(f"Need {need} more pool-verified mono-W cards")

# List extra fill candidates not yet used
extra = []
for name, e in pool.items():
    if name in seen:
        continue
    if not monoW_legal(name, e):
        continue
    typ = (e.get("type_line") or "")
    if "Land" in typ:
        continue  # prefer spells for fill
    extra.append((name, e.get("qty", 0), e.get("mana_cost") or "?"))
extra.sort(key=lambda x: -x[1])
print("\nTop fill candidates:")
for n, q, m in extra[:40]:
    print(f"  {n} | qty={q} | {m}")
