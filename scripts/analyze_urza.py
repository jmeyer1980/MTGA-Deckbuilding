#!/usr/bin/env python3
"""Analyze the collection for a mono-U Urza, Lord High Artificer Competitive Brawl deck."""
import json
from collections import Counter

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]

# Confirm commander
urza = pool.get("Urza, Lord High Artificer")
print("=== COMMANDER ===")
if urza:
    print(f"Urza, Lord High Artificer: qty={urza.get('qty')} ci={urza.get('color_identity')} "
          f"brawl={urza.get('brawl')} competitivebrawl={urza.get('competitivebrawl')} "
          f"standard={urza.get('standard')} set={urza.get('set')} cmc={urza.get('cmc')}")
else:
    print("Urza NOT in pool!")
print()

COMMANDER_CI = set(urza.get("color_identity") or []) if urza else {"U"}

# Gather artifacts owned, competitive brawl legal, color identity subset of commander CI
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
    arts.append((name, qty, e.get("cmc"), t, ci, e.get("rarity"), e.get("set")))

arts.sort(key=lambda x: (x[2] or 99, x[0]))
print(f"=== ARTIFACTS OWNED (competitive brawl legal, ci subset of {sorted(COMMANDER_CI)}) ===")
print(f"Total distinct artifact names: {len(arts)}")
print(f"Total artifact copies: {sum(a[1] for a in arts)}")
print()

creatures = [a for a in arts if "Creature" in a[3]]
noncreature = [a for a in arts if "Creature" not in a[3]]
lands = [a for a in arts if "Land" in a[3]]

print(f"Artifact creatures: {len(creatures)} distinct / {sum(a[1] for a in creatures)} copies")
for name, qty, cmc, t, ci, rarity, s in sorted(creatures, key=lambda x: ((x[2] or 99), x[0])):
    print(f"  {qty}x {name:<45} cmc={cmc:<4} ci={sorted(ci)} {t[:55]}")
print()

print(f"Noncreature artifacts: {len(noncreature)} distinct / {sum(a[1] for a in noncreature)} copies")
for name, qty, cmc, t, ci, rarity, s in sorted(noncreature, key=lambda x: ((x[2] or 99), x[0])):
    print(f"  {qty}x {name:<45} cmc={cmc:<4} ci={sorted(ci)} {t[:55]}")
print()

print(f"Artifact lands: {len(lands)} distinct / {sum(a[1] for a in lands)} copies")
for name, qty, cmc, t, ci, rarity, s in sorted(lands, key=lambda x: ((x[2] or 99), x[0])):
    print(f"  {qty}x {name:<45} cmc={cmc:<4} ci={sorted(ci)} {t[:55]}")
print()

curve = Counter()
for name, qty, cmc, t, ci, rarity, s in noncreature:
    if "Land" in t:
        continue
    try:
        mv = int(cmc)
    except (TypeError, ValueError):
        mv = 99
    curve[mv] += qty
print("=== NONCREATURE ARTIFACT CURVE (by copies) ===")
for mv in sorted(curve):
    print(f"  CMC {mv}: {curve[mv]} copies")
print()

colorless = [a for a in arts if not a[4]]
blue = [a for a in arts if a[4]]
print(f"Colorless artifacts: {len(colorless)} distinct / {sum(a[1] for a in colorless)} copies")
print(f"Blue artifacts: {len(blue)} distinct / {sum(a[1] for a in blue)} copies")
print()

key_names = [
    "Arcane Signet", "Mind Stone", "Lightning Greaves", "Command Tower", "Reliquary Tower",
    "Solemn Simulacrum", "Worn Powerstone", "Thran Dynamo", "Coalition Relic",
    "Chromatic Star", "Springleaf Drum", "Aether Vial", "Mox Amber", "Mox Opal",
    "The One Ring", "Urza's Saga", "Urza's Mine", "Urza's Power Plant", "Urza's Tower",
    "Foundry Inspector", "Myr Superion", "Welding Jar", "Scrap Trawler", "Glint Hawk",
    "Karn, Scion of Urza", "Karn, the Great Creator", "Saheeli, the Gifted",
    "Teferi, Temporal Archmage", "Daretti, Scrap Savant", "Tezzeret",
    "Parallel Lives", "Doubling Season", "Anointed Procession", "Mondrak",
]
print("=== KEY ARTIFACT/ENBLER CARDS OWNED ===")
found_key = []
for name, e in pool.items():
    if e.get("qty", 0) <= 0:
        continue
    if e.get("competitivebrawl") != "legal":
        continue
    if name in key_names:
        ci = set(e.get("color_identity") or [])
        ok = ci <= COMMANDER_CI
        found_key.append((name, e.get("qty"), e.get("cmc"), (e.get("type_line") or "")[:45], sorted(ci), ok))
found_key.sort(key=lambda x: (not x[5], x[0]))
for name, qty, cmc, t, ci, ok in found_key:
    flag = "OK " if ok else "OFF-CI"
    print(f"  [{flag}] {qty}x {name:<40} cmc={cmc:<4} ci={ci} | {t}")
print()

print("=== NON-ARTIFACT BLUE/COLORLESS CARDS OWNED (potential payoffs/support) ===")
pay = []
for name, e in pool.items():
    if e.get("qty", 0) <= 0:
        continue
    if e.get("competitivebrawl") != "legal":
        continue
    t = (e.get("type_line") or "")
    if "Artifact" in t:
        continue
    ci = set(e.get("color_identity") or [])
    if not ci <= COMMANDER_CI:
        continue
    pay.append((name, e.get("qty"), e.get("cmc"), t, sorted(ci)))
pay.sort(key=lambda x: ((x[2] or 99), x[0]))
print(f"(pool.json lacks oracle text; listing blue/colorless non-artifacts owned: {len(pay)})")
for name, qty, cmc, t, ci in pay[:70]:
    print(f"  {qty}x {name:<45} cmc={cmc:<4} ci={ci} | {t[:45]}")
print()

print("=== BASIC / NONBASIC LANDS OWNED (ci subset of U) ===")
lands_all = []
for name, e in pool.items():
    if e.get("qty", 0) <= 0:
        continue
    if e.get("competitivebrawl") != "legal":
        continue
    t = (e.get("type_line") or "")
    if "Land" not in t:
        continue
    ci = set(e.get("color_identity") or [])
    if not ci <= COMMANDER_CI:
        continue
    lands_all.append((name, e.get("qty"), t, sorted(ci)))
lands_all.sort(key=lambda x: x[0])
for name, qty, t, ci in lands_all:
    print(f"  {qty}x {name:<45} | {t[:45]} ci={ci}")
print(f"Total land copies: {sum(a[1] for a in lands_all)} distinct: {len(lands_all)}")
