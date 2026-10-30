#!/usr/bin/env python3
"""Build a Standard Brawl deck from pool data (59 unique + 1 commander)."""

import json
import os

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
DECKS_DIR = f"{ROOT}/decks"

# Load pool
with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# Define the commander
COMMANDER = "Giada, Font of Hope"

# Get White cards that are standard legal and Brawl legal
white_cards = []
for name, entry in pool.items():
    ci = entry.get('color_identity') or []
    if 'W' in ci:
        std = entry.get('standard', '')
        brawl = entry.get('brawl', '')
        if std == 'legal' and brawl == 'legal':
            qty = entry.get('qty', 0)
            mana = entry.get('mana_cost') or '?'
            white_cards.append((name, qty, mana))

# Sort by mana
def mana_key(card):
    mana = card[2]
    if mana == '?':
        return (9, 9, 9)
    nums = []
    for part in mana.split('{'):
        nums.append(part.rstrip('}').rstrip('}'))
    # Pad to 5 elements
    while len(nums) < 5:
        nums.append('0')
    return tuple(int(n) if n.isdigit() else 99 for n in nums[:5])

white_cards.sort(key=mana_key)

# Write candidates
candidate_path = f"{DECKS_DIR}/white_candidates.txt"
with open(candidate_path, "w", encoding="utf-8") as f:
    for name, qty, mana in white_cards:
        f.write(f"{name}\t{qty}\t{mana}\n")

print(f"White cards available: {len(white_cards)}")
print("\nTop White cards by quantity:")
for name, qty, mana in sorted(white_cards, key=lambda x: -x[1])[:20]:
    print(f"  {name:<45} qty={qty:>3}  [{mana}]")

print(f"\nWrote {len(white_cards)} candidates to {candidate_path}")
