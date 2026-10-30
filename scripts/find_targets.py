#!/usr/bin/env python3
"""Check pool for target commanders and show basic info."""

import json
import sys

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

targets = []
for name, entry in pool.items():
    n = name.lower()
    if "giada" in n or "aurelia" in n or "font of hope" in n or "warleader" in n:
        targets.append((name, entry))

if not targets:
    print("No matching commanders found in pool!")
    sys.exit(0)

for name, entry in sorted(targets):
    print(f"{name}:")
    print(f"  Copies: {entry.get('qty', 0)}")
    print(f"  Standard: {entry.get('standard', 'NOT CHECKED')}")
    print(f"  Brawl: {entry.get('brawl', 'NOT CHECKED')}")
    print(f"  Competitive Brawl: {entry.get('competitivebrawl', 'NOT CHECKED')}")
    print(f"  Color identity: {entry.get('color_identity', 'N/A')}")
    print(f"  Mana cost: {entry.get('mana_cost', 'N/A')}")
    print(f"  CMC: {entry.get('cmc', 'N/A')}")
    print()

# Summary
giadas = [(n, e) for n, e in pool.items() if "giada" in n.lower()]
aurelias = [(n, e) for n, e in pool.items() if "aurelia" in n.lower()]
print(f"Giada-related cards: {len(giadas)}")
print(f"Aurelia-related cards: {len(aurelias)}")

# Count total copies of each
giada_copies = sum(e.get("qty", 0) for n, e in giadas)
aurelia_copies = sum(e.get("qty", 0) for n, e in aurelias)
print(f"Total Giada copies: {giada_copies}")
print(f"Total Aurelia copies: {aurelia_copies}")
