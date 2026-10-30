#!/usr/bin/env python3
"""Add 2 cards to the Standard Brawl deck and re-write it."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
DECK_PATH = f"{ROOT}/decks/standard60-brawl-giada.txt"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)
pool = data["pool"]

# Read current deck
with open(DECK_PATH, encoding="utf-8") as f:
    lines = f.read().strip().split('\n')

# Extract card names (excluding "Deck" line)
deck_cards = []
for line in lines:
    if line.startswith('1 ') and not line.startswith('Deck'):
        name = line.split(' (')[0].strip()
        deck_cards.append(name)

print(f"Current cards: {len(deck_cards)}")

# Check additional cards
additions = [
    "Ajani Resolute",  # Already exists in pool - 1/1 with menace
    "Bilbo's Gambit",  # Already exists
    "Surgical Precision",  # Already exists
    "Healer's Hawk",  # Already exists
    "Resolute Reinforcements",  # Already exists
    "Disenchant",  # Remove old copy and add back
]

for name in additions:
    if name in pool:
        entry = pool[name]
        print(f"  {name}: FOUND qty={entry.get('qty', 0)}, std={entry.get('standard', '')}, mana={entry.get('mana_cost', '?')}")
    else:
        print(f"  {name}: NOT FOUND")

# Need 2 more cards
# Let's pick cards with qty >= 3 and standard legal
extra_cards = ["Ajani Resolute", "Disenchant"]  # Ajani Resolute qty=2, Disenchant qty=4

# For each, check if it's already in the deck
for card in extra_cards:
    if card not in deck_cards:
        entry = pool[card]
        mana = entry.get('mana_cost', '?')
        print(f"\nAdding: {card} ({entry.get('set', '')} {entry.get('card_faces', [{}])[0].get('collector_number', '')} ) mana={mana}")
        
        # Add to deck file
        with open(DECK_PATH, "a", encoding="utf-8") as f:
            f.write(f"1 {card} ({entry.get('set', '')}) {entry.get('card_faces', [{}])[0].get('collector_number', '')}\n")

# Verify
with open(DECK_PATH, encoding="utf-8") as f:
    lines = f.read().strip().split('\n')
print(f"\nFinal count: {len(lines) - 1} cards")
