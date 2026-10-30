#!/usr/bin/env python3
"""Focused Urza artifact inventory: noncreature artifacts, curve, key cards."""
import json
from collections import Counter

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]

COMMANDER_CI = {"U"}

arts = []
for name, e in pool.items():
    qty = e.get("qty", 0)
    if qty <= 0:
        continue
    if e.get("competitivebrawl") != "legal":
        continue
    t = (e.get("type_line") or "")
    if "Artifact" not in t:
        continue
    ci = set(e.get("color_identity") or [])
    if not ci <= COMMANDER_CI:
        continue
    arts.append((name, qty, e.get("cmc"), t, ci))

noncreature = [a for a in arts if "Creature" not in a[3]]
noncreature.sort(key=lambda x: ((x[2] or 99), x[0]))

print("=== NONCREATURE ARTIFACTS (cmc asc) ===")
for name, qty, cmc, t, ci in noncreature:
    print(f"  {qty}x {name:<46} cmc={cmc:<4} ci={sorted(ci)} | {t[:58]}")
print()
print(f"Total noncreature artifact distinct: {len(noncreature)} copies: {sum(a[1] for a in noncreature)}")

curve = Counter()
for name, qty, cmc, t, ci in noncreature:
    if "Land" in t:
        continue
    try:
        mv = int(cmc)
    except (TypeError, ValueError):
        mv = 99
    curve[mv] += qty
print("\n=== NONCREATURE NONLAND ARTIFACT CURVE (by copies) ===")
for mv in sorted(curve):
    bar = "#" * curve[mv]
    print(f"  CMC {mv}: {curve[mv]:>3} {bar}")

# Ramp/mana rocks specifically
print("\n=== MANA ROCKS / RAMP ARTIFACTS OWNED ===")
rock_keywords = ["signet", "talisman", "stone", "dynamo", "coalition", "key", "vial", "mox", "lotus",
                 "pendulum", "prism", "crypt", "monolith", "origin", "bow", "mirror", "sword",
                 "wayfarer", "hexgold", "sol ring", "worn powerstone", "thran"]
rocks = [a for a in noncreature if any(k in a[0].lower() for k in rock_keywords)
         and "Land" not in a[3]]
rocks.sort(key=lambda x: ((x[2] or 99), x[0]))
for name, qty, cmc, t, ci in rocks:
    print(f"  {qty}x {name:<46} cmc={cmc:<4} ci={sorted(ci)} | {t[:58]}")
print(f"Ramp/rock distinct: {len(rocks)} copies: {sum(a[1] for a in rocks)}")

# 0-1 cmc artifacts (cheap fuel for Construct)
print("\n=== CHEAP (0-1 cmc) NONCREATURE ARTIFACTS ===")
cheap = [a for a in noncreature if ("Land" not in a[3]) and (a[2] is not None and a[2] <= 1)]
cheap.sort(key=lambda x: (x[2], x[0]))
for name, qty, cmc, t, ci in cheap:
    print(f"  {qty}x {name:<46} cmc={cmc:<4} ci={sorted(ci)} | {t[:58]}")
print(f"Cheap distinct: {len(cheap)} copies: {sum(a[1] for a in cheap)}")
