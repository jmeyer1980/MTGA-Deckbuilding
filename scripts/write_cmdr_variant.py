#!/usr/bin/env python3
"""Write a Commander-section variant to test brawl-mode parsing."""

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
SRC = f"{ROOT}/decks/standard60-brawl-giada.txt"
DST = f"{ROOT}/decks/standard60-brawl-giada-cmdr.txt"

with open(SRC, encoding="utf-8") as f:
    lines = [l.rstrip("\n") for l in f if l.strip()]

assert lines[0] == "Deck"
cards = lines[1:]
cmdr = [c for c in cards if "Giada" in c]
rest = [c for c in cards if "Giada" not in c]
assert len(cmdr) == 1 and len(rest) == 59, (len(cmdr), len(rest))

with open(DST, "w", encoding="utf-8") as f:
    f.write("Commander\n" + cmdr[0] + "\nDeck\n" + "\n".join(rest) + "\n")
print(f"Wrote {DST}")
