#!/usr/bin/env python3
"""Giada + Aurelia benchmark rows + mono-W depth confirmation."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]

legal_identities = {}
for name, e in pool.items():
    if e.get("qty", 0) < 1:
        continue
    if e.get("standard") != "legal" or e.get("brawl") != "legal":
        continue
    if (e.get("competitivebrawl") or "legal") == "banned":
        continue
    legal_identities[name] = frozenset(e.get("color_identity") or [])

def depth(ci):
    ci = frozenset(ci)
    return sum(1 for c in legal_identities.values() if c <= ci)

for target in ["Giada, Font of Hope", "Aurelia, the Warleader",
               "Aurelia, the Law Above", "Leonardo, Cutting Edge",
               "Thalia, the Survivor", "Danitha, Sword of Hope"]:
    e = pool.get(target)
    if e is None:
        print(f"{target}: NOT IN POOL")
        continue
    ci = sorted(e.get("color_identity") or [])
    print(f"{target} | x{e.get('qty')} | {e.get('mana_cost')} | "
          f"cmc={e.get('cmc')} | ci={ci or ['C']} | depth={depth(ci)} | {e.get('rarity')}")
