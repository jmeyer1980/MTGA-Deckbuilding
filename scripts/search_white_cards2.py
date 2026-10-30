#!/usr/bin/env python3
"""Search for ready alternatives for unfinished cards."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Search for White cards that complete the deck
print("=== WHITE SEARCH ===")
white_keywords = [
    "sanctity", "protection", "faith", "moment", "triumph",
    "bonds", "knight", "regent", "duke", "duke's", "guide", "steward",
    "saviors", "keeper", "guardian", "warden", "paladin", "avenging",
    "invoking", "fervor", "devotion", "holy", "blessing", "seize",
    "battery", "charge", "donate", "augment", "buy", "ritual",
    "delver", "probe", "relevance", "hunter", "scout", "patrol",
    "spy", "intel", "elusive", "stealth", "hidden", "ambush",
    "give", "rescue", "sworn", "oath", "quest", "acceptance",
]

for kw in white_keywords:
    matches = []
    for name, entry in pool.items():
        ci = entry.get("color_identity", [])
        if "W" in ci and kw.lower() in name.lower():
            matches.append((name, entry.get("qty", 0), entry.get("mana_cost", "?"), entry.get("cmc", "?")))
    if matches:
        print(f"\n--- {kw} (White) ---")
        for m in sorted(matches, key=lambda x: -(x[1] or 0)):
            print(f"  {m[0]:<50} qty={m[1]:>3}  {m[2]} cmc={m[3]}  std={pool[m[0]].get('standard','?')}")
