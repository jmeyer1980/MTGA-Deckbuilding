#!/usr/bin/env python3
"""Search pool for specific cards to fix the deck."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Check current cards in deck
current = [
    "Ajani's Pridemate", "Resolute Reinforcements", "Knight's Pledge",
    "Enduring Innocence", "Healer's Hawk", "Way of the Healer",
    "Koth of the Homestead", "Surgical Precision", "Make Your Move",
    "Torment, Oldspell", "Dispel", "Giada, Font of Hope", "Plains", "Island", "Swamp", "Mountain", "Forest"
]

print("=== Current deck cards ===")
for name in current:
    if name in pool:
        entry = pool[name]
        print(f"  {name:<40} qty={entry.get('qty',0):>3}  [{entry.get('mana_cost','?')}] {entry.get('cmc',0)}  std={entry.get('standard','?')}  brawl={entry.get('brawl','?')}")
    else:
        print(f"  {name:<40} NOT FOUND")

# Search for better alternatives
print("\n=== Searching for alternatives ===")
alternatives = {
    "replacement for Torment, Oldspell (board wipe if not standard)": ["turnabout", "demolish", "torment", "sacrifice"],
    "White 3-drop removal": ["blurling", "crown of madness", "dispel", "past in time"],
    "White 2-drop": ["healer's hawk", "ajani's pridemate"],
    "White 3-drop creatures": ["herald of the raven", "serrated navigator"],
    "Removal that is standard legal": ["douse", "press the attack", "power tap"],
}

for cat, keywords in alternatives.items():
    print(f"\n--- {cat} ---")
    for kw in keywords:
        matches = []
        for name, entry in pool.items():
            if kw.lower() in name.lower():
                matches.append((name, entry.get("qty", 0), entry.get("mana_cost", "?"), entry.get("cmc", "?")))
        if matches:
            for m in sorted(matches, key=lambda x: -x[1]):
                print(f"  {m[0]:<50} qty={m[1]:>3}  {m[2]} cmc={m[3]}  std={pool[m[0]].get('standard','?')}")
        else:
            print(f"  {kw}: no matches")
