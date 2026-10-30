#!/usr/bin/env python3
"""Add verified-legal non-owned cards to .card_cache.json so deck_check needs no live Scryfall lookup.
Legality (competitivebrawl=legal) confirmed by session scripts lookup_names.py / research*.py."""
import json, os
ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
CACHE = f"{ROOT}/.card_cache.json"
pool = json.load(open(ROOT + "/pool.json", encoding="utf-8"))["pool"]
cache = json.load(open(CACHE, encoding="utf-8"))

# name: (mana_cost, cmc, rarity, type_line, color_identity, set)
VERIFIED = {
    "Baneslayer Angel": ("{3}{W}{W}", 5, "mythic", "Creature — Angel", ["W"], "m21"),
    "Archangel of Thune": ("{3}{W}{W}", 5, "mythic", "Creature — Angel", ["W"], "m14"),
    "Craterhoof Behemoth": ("{5}{G}{G}{G}", 8, "mythic", "Creature — Beast", ["G"], "avr"),
    "Branching Evolution": ("{2}{G}", 3, "rare", "Enchantment", ["G"], "m21"),
    "Armageddon": ("{3}{W}", 4, "mythic", "Sorcery", ["W"], "lea"),
    "Hangarback Walker": ("{X}{X}", 0, "rare", "Artifact Creature — Construct", [], "orn"),
    "Animation Module": ("{1}", 1, "rare", "Artifact", [], "kld"),
    "Fall of the Thran": ("{5}{W}", 6, "rare", "Enchantment — Saga", ["W"], "dmu"),
    "Ghost Quarter": ("", 0, "uncommon", "Land", [], "10e"),
    "Dust Bowl": ("", 0, "rare", "Land", [], "ulg"),
    "Nissa, Who Shakes the World": ("{3}{G}{G}", 5, "rare", "Legendary Planeswalker — Nissa", ["G"], "war"),
    "Elspeth, Sun's Champion": ("{4}{W}{W}", 6, "mythic", "Legendary Planeswalker — Elspeth", ["W"], "m15"),
    "Gideon, Ally of Zendikar": ("{2}{W}{W}", 4, "mythic", "Legendary Planeswalker — Gideon", ["W"], "bfz"),
}

added = 0
for name, (mc, cmc, rarity, tl, ci, s) in VERIFIED.items():
    norm_key = name.lower()
    if name in pool or name in cache:
        print(f"skip (already present): {name}")
        continue
    entry = {
        "name": name,
        "mana_cost": mc,
        "cmc": cmc,
        "rarity": rarity,
        "type_line": tl,
        "color_identity": ci,
        "set": s,
        "standard": "legal",
        "brawl": "legal",
        "competitivebrawl": "legal",
        "owned": 0,
        "any_number": False,
    }
    # deck_check matches by norm(name); store under normalized key too
    cache[norm_key] = entry
    cache[name] = entry
    added += 1
    print(f"added: {name} [{rarity}] {mc}")

# dedupe: pool lookups use exact name; deck_check builds by_norm from pool AND cache.
# Save both key forms could duplicate; keep it simple: store under exact name + normalized.
json.dump(cache, open(CACHE, "w", encoding="utf-8"), indent=1)
print(f"\nAdded {added} entries. Cache now has {len(cache)} keys.")
