import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

cards = [
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
]

for c in cards:
    if c in pool:
        print(f"{c}: qty={pool[c]['qty']}")
    else:
        print(f"{c}: NOT IN POOL")
