#!/usr/bin/env python3
"""Get full details for target commanders from pool.json."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

targets = ["Giada, Font of Hope", "Aurelia, the Warleader"]

for name in targets:
    if name in pool:
        entry = pool[name]
        print(f"{name}")
        print(f"  Copies: {entry.get('qty', 0)}")
        print(f"  Standard: {entry.get('standard', 'N/A')}")
        print(f"  Brawl (casual): {entry.get('brawl', 'N/A')}")
        print(f"  Competitive Brawl: {entry.get('competitivebrawl', 'N/A')}")
        print(f"  Color identity: {entry.get('color_identity', 'N/A')}")
        print(f"  Mana cost: {entry.get('mana_cost', 'N/A')}")
        print(f"  CMC: {entry.get('cmc', 'N/A')}")
        print(f"  Rarity: {entry.get('rarity', 'N/A')}")
        print(f"  Type line: {entry.get('type_line', 'N/A')}")
        print(f"  Set: {entry.get('set', 'N/A')}")
        print()
    else:
        print(f"{name} NOT FOUND in pool\n")
