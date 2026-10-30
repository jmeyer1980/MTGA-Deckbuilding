#!/usr/bin/env python3
"""Search for land names in pool."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Search for land variants
lands = ["plains", "island", "swamp", "mountain", "forest", "tundra", "tropical"]
for land in lands:
    matches = []
    for name, entry in pool.items():
        if land in name.lower():
            matches.append((name, entry.get("qty", 0)))
    if matches:
        print(f"\n=== {land} ===")
        for n, q in sorted(matches, key=lambda x: -x[1]):
            print(f"  {n:<40} qty={q}")

# Also search for Giada alternatives
print("\n=== Search for removal and other cards ===")
removals = ["douse", "dispel", "interrupt", "press", "power tap", "quench", "sublime", "torment", "sacrifice"]
for r in removals:
    matches = []
    for name, entry in pool.items():
        if r in name.lower():
            matches.append((name, entry.get("qty", 0), entry.get("mana_cost", "?"), entry.get("cmc", "?")))
    if matches:
        print(f"\n--- {r} ---")
        for m in sorted(matches, key=lambda x: -(x[1] or 0)):
            print(f"  {m[0]:<50} qty={m[1]:>3}  {m[2]} cmc={m[3]}  std={pool[m[0]].get('standard','?')}")
    else:
        print(f"\n--- {r}: no matches")
