#!/usr/bin/env python3
"""Check specific card in pool."""

import json

POOL = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# Check several cards
test_cards = [
    "Giada, Font of Hope",
    "Ajani's Pridemate",
    "Turnabout",
    "Ajani Resolute",
    "Mass Recall",
    "Stifle",
]

for name in test_cards:
    if name in pool:
        entry = pool[name]
        print(f"{name}: FOUND")
        print(f"  qty={entry.get('qty', 0)}")
        print(f"  standard={entry.get('standard', 'N/A')}")
        print(f"  brawl={entry.get('brawl', 'N/A')}")
        print(f"  mana={entry.get('mana_cost', 'N/A')}")
    else:
        print(f"{name}: NOT FOUND")
    print()
