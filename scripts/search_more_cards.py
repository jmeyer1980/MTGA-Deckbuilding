#!/usr/bin/env python3
"""Search the pool for more Standard Brawl friendlies."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    data = json.load(f)

pool = data["pool"]

# Categories of cards to search
searches = {
    "Stifles/removal": ["stifle", "stifling", "purge", "dispel", "dispelling", "douse"],
    "Instant spells": ["instant", "flash"],
    "Cards with 'Warrior'": ["warrior", "soldier", "knight", "guardian"],
    "Cards with 'Hunter'": ["hunter", "scout", "patrol"],
    "Cards with 'Spirit'": ["spirit", "ghost", "phantom", "shade", "wisp"],
    "Cards with 'Herald'": ["herald", "messenger", "beacon"],
    "Cards with 'Bonds/Acceptance'": ["bond", "acceptance", "accept"],
    "Cards with 'Mercy/Pity'": ["mercy", "pity", "kindness", "grace"],
    "Cards with 'Triumph'": ["triumph", "victory", "victorious"],
    "Cards with 'Charge/Charge Aura'": ["charge", "awoken"],
    "Cards with 'Archaic'": ["archaic"],
    "Cards with 'Reincarnation'": ["reincarnation", "beloved"],
    "Cards with 'Seal'": ["seal"],
    "Cards with 'Brotherhood'": ["brotherhood", "bonds"],
    "Cards with 'Sharing'": ["sharing", "gift", "gifts"],
    "Cards with 'Defender/Guard'": ["defender", "ward", "guard"],
    "Cards with 'Valor'": ["valor"],
    "Cards with 'Pride'": ["pride"],
    "Cards with 'Consecration'": ["consecration"],
    "Cards with 'Exalted'": ["exalted"],
    "Cards with 'Hero'": ["hero", "heroic"],
]

# Also get all White cards as fallback
all_white = [(n, e) for n, e in pool.items() 
             if 'W' in (e.get('color_identity') or [])]

# Print cards that exist and are relevant
print("=== CHECKING POPULAR CARDS ===")
popular = [
    "Turnabout", "Mass Recall", "Stifle", "Hymn to Tourmaline", 
    "Knight's Vigil", "Enlightened Redemption", "Lost Ambition",
    "Borealis Mastery", "Wayfarer's Faerie", "Healer's Toxin",
    "Gift for M Pardner", "Joyous Flood", "Nim Anthem",
    "Protect the Innocent", "Flashwood", "Gilan, the Great",
    "Kird Ape", "Spires Beesting", "Flash", "Voice of the Mountains",
    "Dovescape", "Bobland Bird", "Gorgon's Orb", "Boom",
    "Pendulum", "Path of Ancestry", "Test Your Mettle",
    "Beneath the Mountain", "Lull", "Numbled",
    "Preserve the Past", "Quick Shot", "The Hero's Charge",
    "Sanctity of the Greens", "Flanking Strike", "Ajani's Pride",
    "Sword of the Clouded Mountain", "Battle Rattle", "Primal Chaos",
    "Silverflash Sprite", "Silverflash Devastator",
    "Test of the Path", "Prayer Beak", "Way of the Monster", "Bludgeon"
]

for name in popular:
    if name in pool:
        entry = pool[name]
        print(f"  FOUND: {name:<40} qty={entry.get('qty', 0)}  [{entry.get('mana_cost','?')}]")
    else:
        print(f"  MISSING: {name:<40}")

print(f"\n=== NON-WHITE CARDS (need to find more) ===")
# Show non-white cards that are plural
non_white = [(n, e) for n, e in pool.items() 
             if 'W' not in (e.get('color_identity') or [])]
print(f"Total non-white cards: {len(non_white)}")
for n, e in sorted(non_white, key=lambda x: -x[1].get('qty', 0))[:50]:
    print(f"  {n:<40} qty={e.get('qty', 0)}  [{e.get('mana_cost','?')}]")
