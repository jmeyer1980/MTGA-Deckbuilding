#!/usr/bin/env python3
"""Inspect Kutzil + GW pool depth for deck build."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
CACHE = f"{ROOT}/.commander_scores.json"

pool = json.load(open(POOL, encoding="utf-8"))["pool"]
e = pool.get("Kutzil, Malamet Exemplar")
print("POOL Kutzil:")
print(json.dumps(e, indent=1))

try:
    cache = json.load(open(CACHE, encoding="utf-8"))
    c = cache.get("Kutzil, Malamet Exemplar")
    if c:
        print("\nSCRYFALL Kutzil:")
        print(f"  mana={c.get('mana_cost')} cmc={c.get('cmc')}")
        print(f"  type={c.get('type_line')}")
        print(f"  text={c.get('oracle_text','')[:600]}")
        print(f"  edhrec={c.get('edhrec_rank')} keywords={c.get('keywords')}")
    else:
        print("\nNo cached Scryfall for Kutzil")
except FileNotFoundError:
    print("\nNo cache file")

# GW legal counts
n_gw = sum(1 for n, x in pool.items()
           if x.get("qty", 0) >= 1 and x.get("standard") == "legal"
           and x.get("brawl") == "legal"
           and set(x.get("color_identity") or []) <= {"G", "W"})
print(f"\nGW-legal pool cards: {n_gw}")

# GW lands in pool, legal
print("\nGW-legal lands (top by qty):")
lands = [(n, x.get("qty", 0), x.get("color_identity"))
         for n, x in pool.items()
         if "Land" in (x.get("type_line") or "")
         and x.get("standard") == "legal" and x.get("brawl") == "legal"
         and set(x.get("color_identity") or []) <= {"G", "W"}]
lands.sort(key=lambda r: -r[1])
for n, q, ci in lands[:30]:
    print(f"  {n} | qty={q} | ci={ci}")
