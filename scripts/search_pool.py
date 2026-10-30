#!/usr/bin/env python3
"""Search pool for White cards relevant to a Giada deck."""

import json
import sys

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Categories to search
categories = {
    "Removes": ["dispel", "force of will", "past in time", "impatience", "crown of madness"],
    "Board Wipes": ["turnabout", "demolish", "torment", "thought curse", "word of command"],
    "Creatures": ["creatures", "knight", "guardian", "warrior", "warhorse"],
    "Giada Synergy": ["endless procession", "light for ancestors", "mercy", "vengeances forge", "seize the moment"],
    "Draw/Ramp": ["idyl of the deep elves", "luster of the veil", "dellwright's remit", "everflowing valoria"],
}

print("Searches in the pool:")
for cat, keywords in categories.items():
    print(f"\n=== {cat} ===")
    for kw in keywords:
        matches = []
        for name, entry in pool.items():
            if kw.lower() in name.lower():
                matches.append((name, entry.get("qty", 0), entry.get("mana_cost", "?")))
        if matches:
            for m in sorted(matches, key=lambda x: -x[1]):
                print(f"  {m[0]:<50} qty={m[1]:>3}  {m[2]}")
        else:
            print(f"  {kw}: no matches")
