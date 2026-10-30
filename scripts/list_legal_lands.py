#!/usr/bin/env python3
"""List lands legal for mono-White Giada (identity subset of W)."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

ok_lands = []
bad_lands = []
for name, entry in pool.items():
    typ = (entry.get("type_line") or "")
    if "Land" not in typ:
        continue
    if entry.get("standard") != "legal" or entry.get("brawl") != "legal":
        continue
    ci = entry.get("color_identity") or []
    if set(ci) <= {"W"}:
        ok_lands.append((name, entry.get("qty", 0), ci, typ[:50]))
    else:
        bad_lands.append((name, entry.get("qty", 0), ci))

ok_lands.sort(key=lambda x: -x[1])
print(f"LEGAL lands for mono-W Giada: {len(ok_lands)}")
for name, qty, ci, typ in ok_lands[:60]:
    print(f"  {name} | qty={qty} | ci={ci} | {typ}")

print(f"\nIllegal (multicolor identity) land examples: {len(bad_lands)}")
for name, qty, ci in sorted(bad_lands, key=lambda x: -x[1])[:20]:
    print(f"  {name} | qty={qty} | ci={ci}")
