#!/usr/bin/env python3
"""Build Standard Brawl (60-card) and Competitive Brawl (100-card) decks around
Kutzil, Malamet Exemplar, and write the deck files directly.

Standard Brawl: 60 cards (1 commander + 59 others), singleton format
Competitive Brawl: 100 cards (1 commander + 99 others), singleton format

Brawl formats are singleton: 1 copy of each non-basic card, up to 4 copies of
basic lands. Brawl also has its own banned list (Standard Brawl is more restrictive).
"""

import os

DECKS = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\decks"

# Standard Brawl (60 cards): 1 commander + 24 basic lands + 35 non-lands
# Non-basic cards are singleton (1 copy each)
sb_deck = [
    (1, "Kutzil, Malamet Exemplar"),

    # Basic lands: 24 (color identity needs G/W lands)
    (4, "Blossoming Sands"),
    (4, "Selesnya Guildgate"),
    (4, "Plains"),
    (4, "Forest"),
    (4, "Mountain"),

    # Non-land cards (singleton - 1 each):
    # Engine creatures (need stacks to draw cards)
    (1, "Ajani's Pridemate"),
    (1, "Leonin Vanguard"),
    (1, "Felidar Savior"),
    (1, "Dawnwing Marshal"),
    # Turn-zero removal/control (set up engine)
    (1, "Banishing Light"),
    (1, "Disenchant"),
    (1, "Repel Calamity"),
    (1, "Ethereal Armor"),
    (1, "Prismatic Undercurrents"),
    (1, "Stasis Snare"),
    # Counters for card advantage
    (1, "Ajani Resolute"),
    # Elect
    (1, "Ajani, Caller of the Pride"),
    # Additional G/W spells
    (1, "Ajani Unrelenting"),
    (1, "Ajani's Anguish"),
    (1, "Ajani's Response"),
    (1, "Ajani's Welcome"),
]

sb_total = sum(c for c, _ in sb_deck)
print(f"Standard Brawl deck: {sb_total} cards")

# Competitive Brawl (100 cards): 1 commander + more cards
cb_deck = [
    (1, "Kutzil, Malamet Exemplar"),

    # Basic lands: 24 (more for longer games)
    (4, "Blossoming Sands"),
    (4, "Selesnya Guildgate"),
    (4, "Plains"),
    (4, "Forest"),
    (4, "Mountain"),
    (4, "Ojer Taq, Deepest Foundation"),

    # Non-land cards (singleton - 1 each):
    (1, "Ajani's Pridemate"),
    (1, "Leonin Vanguard"),
    (1, "Felidar Savior"),
    (1, "Dawnwing Marshal"),
    (1, "Banishing Light"),
    (1, "Disenchant"),
    (1, "Repel Calamity"),
    (1, "Ethereal Armor"),
    (1, "Prismatic Undercurrents"),
    (1, "Stasis Snare"),
    (1, "Ajani Resolute"),
    (1, "Ajani, Caller of the Pride"),
    (1, "Ajani Unrelenting"),
    (1, "Ajani's Anguish"),
    (1, "Ajani's Response"),
    (1, "Ajani's Welcome"),
    (1, "Assemble the Players"),
]

cb_total = sum(c for c, _ in cb_deck)
print(f"Competitive Brawl deck: {cb_total} cards")

# Write the deck files
def write_deck(deck, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("Deck\n")
        for count, name in sorted(deck, key=lambda x: (-x[0], x[1].lower())):
            f.write(f"{count} {name}\n")

sb_path = os.path.join(DECKS, "standard60-brawl-kutzil.txt")
cb_path = os.path.join(DECKS, "brawl100-kutzil.txt")

write_deck(sb_deck, sb_path)
write_deck(cb_deck, cb_path)

print(f"\nWritten:")
print(f"  {sb_path}")
print(f"  {cb_path}")
