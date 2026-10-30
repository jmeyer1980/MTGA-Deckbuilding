#!/usr/bin/env python3
import json
pool = json.load(open("pool.json", encoding="utf-8"))["pool"]
owned = [(n, x) for n, x in pool.items()
         if x.get("qty", 0) >= 1
         and x.get("competitivebrawl") == "legal"
         and set(x.get("color_identity") or []) <= {"G", "W"}]

print("=== OWNED RARES/MYTHICS (GW competitive-legal) ===")
hi = [(n, x) for n, x in owned if x["rarity"] in ("rare", "mythic")]
for n, x in sorted(hi):
    print(f"  {x['rarity']:<7} {x['qty']}x  {n:<42} {x.get('type_line','')[:48]}")

print("\n=== OWNED LANDS (GW competitive-legal) ===")
for n, x in sorted([o for o in owned if "Land" in o[1].get("type_line", "")]):
    print(f"  {x['rarity']:<7} {x['qty']}x  {n}")

print("\n=== OWNED PLANESWALKERS (GW competitive-legal) ===")
for n, x in sorted([o for o in owned if "Planeswalker" in o[1].get("type_line", "")]):
    print(f"  {x['rarity']:<7} {x['qty']}x  {n}")

print("\n=== KEY UNCOMMONS (removal/protection/ramp) ===")
for n, x in sorted([o for o in owned if o[1]["rarity"] == "uncommon"]):
    t = x.get("type_line", "")
    print(f"  {x['qty']}x  {n:<42} {t[:48]}")
