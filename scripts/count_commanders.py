#!/usr/bin/env python3
"""Count owned Standard-Brawl-eligible commanders in the pool."""

import json
from collections import Counter

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]

eligible = []
for name, e in pool.items():
    if e.get("qty", 0) < 1:
        continue
    typ = e.get("type_line") or ""
    if "Legendary" not in typ or "Creature" not in typ:
        continue
    if e.get("standard") != "legal":
        continue
    if e.get("brawl") != "legal":
        continue
    if (e.get("competitivebrawl") or "legal") == "banned":
        continue
    ci = tuple(sorted(e.get("color_identity") or []))
    eligible.append((name, e.get("qty", 0), e.get("cmc", 0),
                     e.get("mana_cost") or "?", ci, e.get("rarity", "?")))

print(f"Eligible owned commanders: {len(eligible)}")
print("\nBy color count:")
cc = Counter(len(ci) for _, _, _, _, ci, _ in eligible)
for n in sorted(cc):
    print(f"  {n}-color: {cc[n]}")

print("\nBy MV bucket:")
mv = Counter(int(c) if c == int(c) else "X" for _, _, c, _, _, _ in eligible)
for k in sorted(mv, key=str):
    print(f"  MV {k}: {mv[k]}")

print("\nCheapest (MV <= 3), sorted by MV then name:")
for row in sorted(eligible, key=lambda r: (r[2], r[0]))[:40]:
    name, qty, cmc, mana, ci, rar = row
    print(f"  {name} | x{qty} | {mana} | ci={list(ci) or ['C']} | {rar}")
