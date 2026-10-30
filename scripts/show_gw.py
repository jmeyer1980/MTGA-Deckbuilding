import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

# G/W cards for Kutzil deck
gw_cards = [
    "Kutzil, Malamet Exemplar",
    "Blossoming Sands",
    "Plains",
    "Forest",
    "Mountain",
    "Selesnya Guildgate",
    "Ajani's Pridemate",
    "Leonin Vanguard",
    "Felidar Savior",
    "Dawnwing Marshal",
    "Banishing Light",
    "Disenchant",
    "Repel Calamity",
    "Ethereal Armor",
    "Prismatic Undercurrents",
    "Stasis Snare",
    "Ajani Resolute",
    "Ajani, Caller of the Pride",
    "Assemble the Players",
    "Ojer Taq, Deepest Foundation",
    "Elder Mountain",
    "Gautam, the Weave Weaver",
    "Birch, the Lifecutter",
    "Jaya, Voice of the Elements",
    "Melira, Sylvan Spirit",
    "Providence of the Pack",
    "Withering Spires",
    "Humble Housemate",
    "Tough-Tusk Boar",
    "Berserker Axe",
    "Asht",
    "Jace, the Mind Sculptor",
    "Painful Malady",
    "Gaia's Benefit",
]

print(f"Total cards in pool: {len(pool)}")
print("\nG/W Kutzil-related cards found in pool:")
count = 0
for c in gw_cards:
    if c in pool:
        print(f"  YES: {c}: qty={pool[c]['qty']}")
        count += 1
    else:
        print(f"  NO: {c}")

print(f"\nFound {count}/{len(gw_cards)} cards")
