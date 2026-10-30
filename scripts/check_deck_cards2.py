#!/usr/bin/env python3
"""Check which cards in the deck exist in the pool."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Read the deck
with open(f"{ROOT}/decks/standard60-brawl-giada.txt", encoding="utf-8") as f:
    deck_lines = f.read().strip().split('\n')

# Extract card names
deck_cards = []
for line in deck_lines:
    if line.startswith('1 ') and not line.startswith('Deck'):
        parts = line.split(' ', 1)
        card_name = parts[1].split(' (')[0].strip()
        deck_cards.append(card_name)

print(f"Total cards in deck: {len(deck_cards)}\n")

# Check each card
missing = []
for card in deck_cards:
    if card in pool:
        entry = pool[card]
        print(f"  {card:<40} FOUND  qty={entry.get('qty', 0)}")
    else:
        missing.append(card)
        print(f"  {card:<40} NOT FOUND")

print(f"\nMissing cards: {len(missing)}")
for m in missing:
    print(f"  - {m}")
