#!/usr/bin/env python3
"""Build a 60-card Standard Brawl deck around Giada, Font of Hope."""

deck_content = """Deck
7 Ajani's Pridemate (LCI) 803
11 Resolute Reinforcements (LCI) 807
2 Enduring Innocence (FDN) 748
7 Healer's Hawk (KLD) 94
4 Way of the Healer (LRI) 13
2 Koth of the Homestead (LCI) 804
2 Surgical Precision (C13) 20
2 Make Your Move (FDN) 70
1 Moment of Triumph (KLD) 106
1 Giada, Font of Hope (FDN) 722
12 Plains (HOB) 194
3 Island (LCI) 867
2 Swamp (LCI) 867
2 Mountain (LCI) 867
2 Forest (LCI) 867
"""

deck_path = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding/decks/standard60-giada-font-of-hope.txt"
with open(deck_path, "w", encoding="utf-8") as f:
    f.write(deck_content)

total = sum(int(line.split()[0]) for line in deck_content.strip().splitlines()
            if line.strip() and not line.startswith('Deck'))
print(f"Written to {deck_path}")
print(f"Total cards: {total}")
