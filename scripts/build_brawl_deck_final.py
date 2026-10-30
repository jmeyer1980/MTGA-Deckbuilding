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

# Commander - 4 elements (name, set, collector, type)
deck.append(("Giada, Font of Hope", "FDN", 722, "commander"))

# Lands - 4 elements each
deck.extend([
    ("Plains", "HOB", 194, "land"),
    ("Island", "LCI", 867, "land"),
    ("Swamp", "LCI", 867, "land"),
    ("Mountain", "LCI", 867, "land"),
    ("Forest", "LCI", 867, "land"),
    ("Buried Waste", "KDO", 673, "land"),
    ("Mire of the Grave", "EXP", 717, "land"),
    ("Scale Spout", "LWV", 490, "land"),
    ("Sorath's Wall", "TMP", 519, "land"),
    ("Void Waltz", "KLD", 733, "land"),
    ("Bramblewood Knoll", "LWV", 486, "land"),
    ("Ghostly Fevered Wood", "KLD", 733, "land"),
    ("Fossil Island", "NBR", 665, "land"),
    ("Twin Lighthouses", "TJ14", 510, "land"),
    ("Sun-Crown Dragons", "WSBJ", 327, "land"),
    ("Tangled Depths", "BN4", 487, "land"),
    ("Wolf's Ruin", "PP2", 375, "land"),
    ("Inzymar's Crag", "BHMT", 468, "land"),
    ("Giant's Stair", "JVC", 343, "land"),
    ("Jaspergarden", "MSW", 449, "land"),
    ("Boulders Barricade", "GS7", 485, "land"),
    ("Slumbering Dragon", "PP2", 364, "land"),
    ("Flood's Edge", "BHMT", 464, "land"),
    ("Barrens Academy", "JVC", 351, "land"),
    ("Basalt Moor", "TP4", 392, "land"),
])

# Creatures - 4 elements each
deck.extend([
    ("Ajani's Pridemate", "LCI", 803, "creature"),
    ("Resolute Reinforcements", "LCI", 807, "creature"),
    ("Healer's Hawk", "KLD", 94, "creature"),
    ("Way of the Healer", "LRI", 13, "creature"),
    ("Koth of the Homestead", "LCI", 804, "creature"),
    ("Serra Angel", "LRI", 415, "creature"),
    ("Elspeth, Storm Slayer", "TDM", 13, "creature"),
    ("Gift for M Pardner", "FDN", 715, "creature"),
    ("Fateshaper Aspirant", "FDN", 613, "creature"),
    ("Wayfarer's Faerie", "KLD", 622, "creature"),
])

# Plant - 4 elements each
deck.extend([
    ("Banishing Light", "C20", 755, "plant"),
    ("Sanctity of the Greens", "FDN", 716, "plant"),
    ("Bodhisattva of the Siskey", "LRI", 613, "plant"),
    ("Slithering Maiden", "LWV", 493, "plant"),
    ("Venerated Basilisk", "FLC", 708, "plant"),
    ("Divine Favor", "LRI", 623, "plant"),
    ("Heart of the Mountain", "LWV", 489, "plant"),
    ("Order of the Pure Light", "KLD", 733, "plant"),
    ("Temple of Silence", "FDN", 704, "plant"),
    ("Hearts of Eldercat", "HOB", 130, "plant"),
])

# Removal - 4 elements each
deck.extend([
    ("Stifle", "FDN", 705, "removal"),
    ("Mass Recall", "FDN", 714, "removal"),
    ("Turnabout", "NWR", 1254, "removal"),
    ("Surgical Precision", "C13", 20, "removal"),
    ("Make Your Move", "FDN", 70, "removal"),
])

# Other - 4 elements each
deck.extend([
    ("Ajani, Caller of the Pride", "FDN", 134, "other"),
    ("Borealis Mastery", "LDN", 14, "other"),
    ("Lost Ambition", "FOD", 158, "other"),
    ("Enlightened Redemption", "FDN", 706, "other"),
    ("Nim Anthem", "KV", 107, "other"),
    ("Ajani Resolute", "LCI", 811, "other"),
    ("Bilbo's Gambit", "FDN", 748, "other"),
    ("Predictive Preparations", "FDN", 708, "other"),
    ("Timid Shieldbearer", "HOB", 107, "other"),
])

# Remove duplicates
seen = set()
unique_deck = []
for d in deck:
    if d[0] not in seen:
        seen.add(d[0])
        unique_deck.append(d)

deck = unique_deck

# Verify we have exactly 60
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
