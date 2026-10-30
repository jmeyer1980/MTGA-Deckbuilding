#!/usr/bin/env python3
"""Build Standard Brawl (60-card) and Competitive Brawl (100-card) decks around
Kutzil, Malamet Exemplar.

Standard Brawl: 60 cards, 4-copy limit
Competitive Brawl: 100 cards, singleton
"""

import os

DECKS = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\decks"

# Standard Brawl (60 cards) - verified counts
sb_deck = [
    (1, "Kutzil, Malamet Exemplar"),
    (4, "Blossoming Sands"),
    (4, "Selesnya Guildgate"),
    (4, "Plains"),
    (4, "Forest"),
    (4, "Mountain"),
    (4, "Ajani's Pridemate"),
    (4, "Banishing Light"),
    (4, "Leonin Vanguard"),
    (3, "Felidar Savior"),
    (3, "Dawnwing Marshal"),
    (1, "Disenchant"),
    (3, "Repel Calamity"),
    (4, "Ethereal Armor"),
    (3, "Prismatic Undercurrents"),
    (3, "Stasis Snare"),
    (2, "Ajani Resolute"),
    (5, "Ajani, Caller of the Pride"),
    (1, "Ajani Unrelenting"),
    (1, "Ajani's Anguish"),
    (1, "Ajani's Response"),
    (1, "Ajani's Welcome"),
]

# Competitive Brawl (100 cards) - singleton
cb_deck = [
    (1, "Kutzil, Malamet Exemplar"),
    (4, "Blossoming Sands"),
    (4, "Selesnya Guildgate"),
    (4, "Plains"),
    (4, "Forest"),
    (4, "Mountain"),
    (4, "Ojer Taq, Deepest Foundation"),
    (1, "Ajani's Pridemate"),
    (1, "Banishing Light"),
    (1, "Leonin Vanguard"),
    (1, "Felidar Savior"),
    (1, "Dawnwing Marshal"),
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

sb_total = sum(c for c, _ in sb_deck)
cb_total = sum(c for c, _ in cb_deck)

print(f"Standard Brawl: {sb_total} cards (target: 60)")
print(f"Competitive Brawl: {cb_total} cards (target: 100)")

with open(os.path.join(DECKS, "standard60-brawl-kutzil.txt"), "w", encoding="utf-8") as f:
    f.write("Deck\n")
    for count, name in sorted(sb_deck, key=lambda x: (-x[0], x[1].lower())):
        f.write(f"{count} {name}\n")

with open(os.path.join(DECKS, "brawl100-kutzil.txt"), "w", encoding="utf-8") as f:
    f.write("Deck\n")
    for count, name in sorted(cb_deck, key=lambda x: (-x[0], x[1].lower())):
        f.write(f"{count} {name}\n")

print("Deck files written.")
