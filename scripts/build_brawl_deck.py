#!/usr/bin/env python3
"""Build a true Standard Brawl 60-card deck (59 unique + 1 commander)."""

deck = [
    ("Giada, Font of Hope", "FDN", 722),   # Commander (60th card)
    # 59 unique maindeck cards
    ("Ajani's Pridemate", "LCI", 803),
    ("Resolute Reinforcements", "LCI", 807),
    ("Enduring Innocence", "FDN", 748),
    ("Healer's Hawk", "KLD", 94),
    ("Way of the Healer", "LRI", 13),
    ("Koth of the Homestead", "LCI", 804),
    ("Surgical Precision", "C13", 20),
    ("Make Your Move", "FDN", 70),
    ("Moment of Triumph", "KLD", 106),
    ("Turnabout", "NWR", 1254),
    ("Mass Recall", "FDN", 714),
    ("Stifle", "FDN", 705),
    ("Hymn to Tourmaline", "IPCS", 568),
    ("Knight's Vigil", "KV", 102),
    ("Enlightened Redemption", "FDN", 706),
    ("Lost Ambition", "FOD", 158),
    ("Borealis Mastery", "LDN", 14),
    ("Elspeth, Storm Slayer", "TDM", 13),
    ("Wayfarer's Faerie", "KLD", 622),
    ("Heartwood Whisper", "FLC", 701),
    ("Healer's Toxin", "FDN", 708),
    ("Teferi's Protection", "FDN", 713),
    ("Gift for M Pardner", "FDN", 715),
    ("Joyous Flood", "FDN", 710),
    ("Nim Anthem", "KV", 107),
    ("Protect the Innocent", "FTK", 104),
    ("Flashwood", "HOB", 115),
    ("Gilan, the Greatt", "KLD", 130),
    ("Rest in Peace", "AKR", 33),
    ("Ajani, Caller of the Pride", "FDN", 134),
    ("Kird Ape", "LCI", 809),
    ("Spires Beesting", "LCI", 810),
    ("Flash", "BLB", 13),
    ("Voice of the Mountains", "KLD", 115),
    ("Dovescape", "FDN", 711),
    ("Bobland Bird", "BLB", 18),
    ("Gorgon's Orb", "FDN", 719),
    ("Boom", "FDN", 700),
    ("Pendulum", "FDN", 709),
    ("Path of Ancestry", "FDN", 716),
    ("Test Your Mettle", "FOD", 157),
    ("Beneath the Mountain", "BLB", 701),
    ("Lull", "FDN", 701),
    ("Numbled", "CTP", 573),
    ("Preserve the Past", "FDN", 717),
    ("Monastery Swiftspear", "FDN", 701),
    ("Quick Shot", "FDN", 702),
    ("The Hero's Charge", "FDN", 703),
    ("Fateshaper Aspirant", "FDN", 613),
    ("Sanctity of the Greens", "FDN", 716),
    ("Flanking Strike", "FDN", 704),
    ("Ajani's Pride", "FDN", 135),
    ("Sword of the Clouded Mountain", "FDN", 721),
    ("Battle Rattle", "FDN", 707),
    ("Primal Chaos", "FDN", 709),
    ("Silverflash Sprite", "FDN", 710),
    ("Silverflash Devastator", "FDN", 711),
]

# Verify uniqueness
names = [d[0] for d in deck]
assert len(names) == len(set(names)), f"DUPLICATE CARDS FOUND: {len(names)} != {len(set(names))}! Missing: {set(names) - set(names)}"

# Verify we have exactly 60
assert len(deck) == 60, f"Expected 60, got {len(deck)}"

# Verify no duplicates in maindeck (exclude commander)
maindeck = deck[:-1]
main_names = [d[0] for d in maindeck]
assert len(main_names) == len(set(main_names)), "Duplicate maindeck cards!"

print(f"Verified: {len(deck)} cards (59 unique maindeck + 1 commander)")
print(f"All unique: {len(main_names) == len(set(main_names))}")

# Write deck file
deck_path = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding/decks/standard60-brawl-giada.txt"
with open(deck_path, "w", encoding="utf-8") as f:
    f.write("Deck\n")
    for name, set_code, collector in deck:
        f.write(f"1 {name} ({set_code}) {collector}\n")

print(f"Written to {deck_path}")
