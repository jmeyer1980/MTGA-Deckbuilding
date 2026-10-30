#!/usr/bin/env python3
"""List top legal White cards in the pool for deck building."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

legal_white = []
for name, entry in pool.items():
    ci = entry.get("color_identity") or []
    if "W" in ci and entry.get("standard") == "legal" and entry.get("brawl") == "legal":
        qty = entry.get("qty", 0)
        mana = entry.get("mana_cost") or "?"
        typ = entry.get("type_line") or "?"
        legal_white.append((name, qty, mana, typ))

legal_white.sort(key=lambda x: -x[1])

print(f"Legal White cards: {len(legal_white)}")
for name, qty, mana, typ in legal_white[:80]:
    print(f"  {name} | qty={qty} | {mana} | {typ[:40]}")
