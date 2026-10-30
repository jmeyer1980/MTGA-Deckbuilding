#!/usr/bin/env python3
"""Check which deck cards exist in pool."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# Read deck file
with open(f"{ROOT}/decks/standard60-brawl-giada.txt", encoding="utf-8") as f:
    lines = f.read().strip().split('\n')

deck_names = []
for line in lines:
    if line.startswith('1 ') and not line.startswith('Deck'):
        name = line.split(' (')[0].strip()
        deck_names.append(name)

print(f"Total cards: {len(deck_names)}\n")

missing = []
found = []
for name in deck_names:
    if name in pool:
        found.append(name)
    else:
        missing.append(name)

print(f"FOUND in pool: {len(found)}")
for name in sorted(found):
    print(f"  {name}")

print(f"\nMISSING from pool: {len(missing)}")
for name in sorted(missing):
    print(f"  {name}")
