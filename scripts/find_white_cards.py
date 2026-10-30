#!/usr/bin/env python3
"""Find White cards and White removal for a Standard Brawl deck."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Search for White cards
print("=== WHITE CARDS (color_identity contains W) ===")
white_cards = []
for name, entry in pool.items():
    ci = entry.get("color_identity", [])
    if "W" in ci:
        white_cards.append((name, entry))

white_cards.sort(key=lambda x: -x[1].get("qty", 0))
for name, entry in white_cards:
    print(f"  {name:<55} qty={entry.get('qty',0):>3}  [{entry.get('mana_cost','?')}] {entry.get('cmc',0)}")
