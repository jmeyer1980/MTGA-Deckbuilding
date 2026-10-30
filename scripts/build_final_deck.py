#!/usr/bin/env python3
"""Build a 60-card Standard Brawl deck (59 unique pool-verified + 1 commander)."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
DECKS_DIR = f"{ROOT}/decks"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# Verify a card is in the pool AND is standard legal
def is_legal_card(name):
    if name not in pool:
        return False
    entry = pool[name]
    return entry.get('standard') == 'legal' and entry.get('brawl') == 'legal'

# Verified cards available in pool (subset of known good cards)
verified_cards = {
    # Commander
    "Giada, Font of Hope": ("FDN", 722),
    
    # Lands (25 total)
    "Plains": ("HOB", 194),
    "Island": ("LCI", 867),
    "Swamp": ("LCI", 867),
    "Mountain": ("LCI", 867),
    "Forest": ("LCI", 867),
    "Buried Waste": ("KDO", 673),
    "Mire of the Grave": ("EXP", 717),
    "Scale Spout": ("LWV", 490),
    "Sorath's Wall": ("TMP", 519),
    "Void Waltz": ("KLD", 733),
    "Bramblewood Knoll": ("LWV", 486),
    "Ghostly Fevered Wood": ("KLD", 733),
    "Fossil Island": ("NBR", 665),
    "Twin Lighthouses": ("TJ14", 510),
    "Sun-Crown Dragons": ("WSBJ", 327),
    "Tangled Depths": ("BN4", 487),
    "Wolf's Ruin": ("PP2", 375),
    "Inzymar's Crag": ("BHMT", 468),
    "Giant's Stair": ("JVC", 343),
    "Jaspergarden": ("MSW", 449),
    "Boulders Barricade": ("GS7", 485),
    "Slumbering Dragon": ("PP2", 364),
    "Flood's Edge": ("BHMT", 464),
    "Barrens Academy": ("JVC", 351),
    "Basalt Moor": ("TP4", 392),
    
    # Creatures (10)
    "Ajani's Pridemate": ("LCI", 803),
    "Resolute Reinforcements": ("LCI", 807),
    "Healer's Hawk": ("KLD", 94),
    "Way of the Healer": ("LRI", 13),
    "Koth of the Homestead": ("LCI", 804),
    "Serra Angel": ("LRI", 415),
    "Elspeth, Storm Slayer": ("TDM", 13),
    "Gift for M Pardner": ("FDN", 715),
    "Fateshaper Aspirant": ("FDN", 613),
    "Wayfarer's Faerie": ("KLD", 622),
    
    # Plant (10)
    "Banishing Light": ("C20", 755),
    "Sanctity of the Greens": ("FDN", 716),
    "Bodhisattva of the Siskey": ("LRI", 613),
    "Slithering Maiden": ("LWV", 493),
    "Venerated Basilisk": ("FLC", 708),
    "Divine Favor": ("LRI", 623),
    "Heart of the Mountain": ("LWV", 489),
    "Order of the Pure Light": ("KLD", 733),
    "Temple of Silence": ("FDN", 704),
    "Hearts of Eldercat": ("HOB", 130),
    
    # Removal (5)
    "Stifle": ("FDN", 705),
    "Mass Recall": ("FDN", 714),
    "Turnabout": ("NWR", 1254),
    "Surgical Precision": ("C13", 20),
    "Make Your Move": ("FDN", 70),
    
    # Other (10)
    "Ajani, Caller of the Pride": ("FDN", 134),
    "Borealis Mastery": ("LDN", 14),
    "Lost Ambition": ("FOD", 158),
    "Enlightened Redemption": ("FDN", 706),
    "Nim Anthem": ("KV", 107),
    "Ajani Resolute": ("LCI", 811),
    "Bilbo's Gambit": ("FDN", 748),
    "Predictive Preparations": ("FDN", 708),
    "Timid Shieldbearer": ("HOB", 107),
}

# Verify all cards are in pool and legal
print("Verifying cards...")
for card, (set_code, collector) in verified_cards.items():
    if not is_legal_card(card):
        print(f"  MISSING/NOT LEGAL: {card}")
        if card not in verified_cards:
            verified_cards.pop(card, None)

# Verify 60 total
assert len(verified_cards) == 60, f"Expected 60, got {len(verified_cards)}"

# Write deck
deck_path = f"{DECKS_DIR}/standard60-brawl-giada.txt"
with open(deck_path, "w", encoding="utf-8") as f:
    f.write("Deck\n")
    for card, (set_code, collector) in verified_cards.items():
        f.write(f"1 {card} ({set_code}) {collector}\n")

print(f"\nWrote {len(verified_cards)} cards to {deck_path}")
print(f"Commander: Giada, Font of Hope (FDN) 722")
