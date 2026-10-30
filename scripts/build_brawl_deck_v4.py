#!/usr/bin/env python3
"""Build a 60-card Standard Brawl deck (59 unique + 1 commander)."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
DECKS_DIR = f"{ROOT}/decks"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# Build deck
deck = []

# Commander
deck.append(("Giada, Font of Hope", "FDN", 722, "commander"))

# Lands (25 total)
deck.extend([
    ("Plains", "HOB", 194),
    ("Island", "LCI", 867),
    ("Swamp", "LCI", 867),
    ("Mountain", "LCI", 867),
    ("Forest", "LCI", 867),
    ("Buried Waste", "KDO", 673),
    ("Mire of the Grave", "EXP", 717),
    ("Scale Spout", "LWV", 490),
    ("Sorath's Wall", "TMP", 519),
    ("Void Waltz", "KLD", 733),
    ("Bramblewood Knoll", "LWV", 486),
    ("Ghostly Fevered Wood", "KLD", 733),
    ("Fossil Island", "NBR", 665),
    ("Twin Lighthouses", "TJ14", 510),
    ("Sun-Crown Dragons", "WSBJ", 327),
    ("Tangled Depths", "BN4", 487),
    ("Wolf's Ruin", "PP2", 375),
    ("Inzymar's Crag", "BHMT", 468),
    ("Giant's Stair", "JVC", 343),
    ("Jaspergarden", "MSW", 449),
    ("Boulders Barricade", "GS7", 485),
    ("Slumbering Dragon", "PP2", 364),
    ("Flood's Edge", "BHMT", 464),
    ("Barrens Academy", "JVC", 351),
    ("Basalt Moor", "TP4", 392),
])

# Creatures (10)
deck.extend([
    ("Ajani's Pridemate", "LCI", 803),
    ("Resolute Reinforcements", "LCI", 807),
    ("Healer's Hawk", "KLD", 94),
    ("Way of the Healer", "LRI", 13),
    ("Koth of the Homestead", "LCI", 804),
    ("Serra Angel", "LRI", 415),
    ("Elspeth, Storm Slayer", "TDM", 13),
    ("Gift for M Pardner", "FDN", 715),
    ("Fateshaper Aspirant", "FDN", 613),
    ("Wayfarer's Faerie", "KLD", 622),
])

# Plant (10)
deck.extend([
    ("Banishing Light", "C20", 755),
    ("Sanctity of the Greens", "FDN", 716),
    ("Bodhisattva of the Siskey", "LRI", 613),
    ("Slithering Maiden", "LWV", 493),
    ("Venerated Basilisk", "FLC", 708),
    ("Divine Favor", "LRI", 623),
    ("Heart of the Mountain", "LWV", 489),
    ("Order of the Pure Light", "KLD", 733),
    ("Temple of Silence", "FDN", 704),
    ("Hearts of Eldercat", "HOB", 130),
])

# Removal (5)
deck.extend([
    ("Stifle", "FDN", 705),
    ("Mass Recall", "FDN", 714),
    ("Turnabout", "NWR", 1254),
    ("Surgical Precision", "C13", 20),
    ("Make Your Move", "FDN", 70),
])

# Other (10)
deck.extend([
    ("Ajani, Caller of the Pride", "FDN", 134),
    ("Borealis Mastery", "LDN", 14),
    ("Lost Ambition", "FOD", 158),
    ("Enlightened Redemption", "FDN", 706),
    ("Nim Anthem", "KV", 107),
    ("Ajani Resolute", "LCI", 811),
    ("Bilbo's Gambit", "FDN", 748),
    ("Predictive Preparations", "FDN", 708),
    ("Timid Shieldbearer", "HOB", 107),
    ("The Eagles Are Coming!", "LCI", 811),
])

# Remove duplicates
seen = set()
unique_deck = []
for d in deck:
    if d[0] not in seen:
        seen.add(d[0])
        unique_deck.append(d)

deck = unique_deck

# Verify
assert len(deck) == 60, f"Expected 60, got {len(deck)}: {[d[0] for d in deck]}"

names = [d[0] for d in deck]
assert len(names) == len(set(names)), f"Duplicates: {set(names) - set(names)}"

# Write deck
deck_path = f"{DECKS_DIR}/standard60-brawl-giada.txt"
with open(deck_path, "w", encoding="utf-8") as f:
    f.write("Deck\n")
    for name, set_code, collector, _ in deck:
        f.write(f"1 {name} ({set_code}) {collector}\n")

print(f"Wrote {len(deck)-1} maindeck + 1 commander = {len(deck)} total cards")
print(f"To: {deck_path}")

# List cards
for name, set_code, collector, _ in deck:
    print(f"  1 {name} ({set_code}) {collector}")
