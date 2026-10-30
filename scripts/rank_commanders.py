#!/usr/bin/env python3
"""Rank owned commanders by deepest owned support (pool-verified legal cards in identity)."""

import json
from collections import Counter

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]

# Precompute legal card color identities
legal_identities = {}
for name, e in pool.items():
    if e.get("qty", 0) < 1:
        continue
    if e.get("standard") != "legal" or e.get("brawl") != "legal":
        continue
    if (e.get("competitivebrawl") or "legal") == "banned":
        continue
    ci = frozenset(e.get("color_identity") or [])
    legal_identities[name] = ci

print(f"Total pool-verified legal cards: {len(legal_identities)}")

# Support depth per color-identity frozenset (cache)
from functools import lru_cache

identity_sets = {}
for ci in set(legal_identities.values()):
    identity_sets[ci] = sum(1 for c in legal_identities.values() if c <= ci)

print(f"\nDistinct identity subsets in pool: {len(identity_sets)}")
print("\nSupport depth by single color (+colorless):")
for c in ["W", "U", "B", "R", "G"]:
    key = frozenset([c])
    print(f"  {c}: {identity_sets.get(key, 0)}")

print("\nSupport depth by 2-color pair:")
pairs = [["W", "U"], ["W", "B"], ["W", "R"], ["W", "G"],
         ["U", "B"], ["U", "R"], ["U", "G"],
         ["B", "R"], ["B", "G"], ["R", "G"]]
for p in pairs:
    key = frozenset(p)
    print(f"  {''.join(p)}: {identity_sets.get(key, 0)}")

# Now rank actual commanders
eligible = []
for name, e in pool.items():
    if e.get("qty", 0) < 1:
        continue
    typ = e.get("type_line") or ""
    if "Legendary" not in typ or "Creature" not in typ:
        continue
    if e.get("standard") != "legal" or e.get("brawl") != "legal":
        continue
    if (e.get("competitivebrawl") or "legal") == "banned":
        continue
    ci = frozenset(e.get("color_identity") or [])
    depth = identity_sets.get(ci, sum(1 for c in legal_identities.values() if c <= ci))
    eligible.append((name, e.get("qty", 0), e.get("cmc", 99),
                     e.get("mana_cost") or "?", sorted(ci),
                     e.get("rarity", "?"), depth))

eligible.sort(key=lambda r: -r[6])

print(f"\n=== Top 30 by support depth ===")
for row in eligible[:30]:
    name, qty, cmc, mana, ci, rar, depth = row
    print(f"  {depth:>4}  {name} | x{qty} | {mana} | ci={ci or ['C']} | {rar}")

print(f"\n=== Top mono-White (your Giada benchmark) ===")
monoW = [r for r in eligible if r[4] == ["W"]]
monoW.sort(key=lambda r: -r[6])
for row in monoW[:15]:
    name, qty, cmc, mana, ci, rar, depth = row
    print(f"  {depth:>4}  {name} | x{qty} | {mana} | {rar}")
