import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

cards = [
    "Kutzil, Malamet Exemplar",
    "Ajani's Pridemate",
    "Banishing Light",
    "Leonin Vanguard",
    "Felidar Savior",
    "Dawnwing Marshal",
    "Disenchant",
    "Repel Calamity",
    "Ethereal Armor",
    "Prismatic Undercurrents",
    "Stasis Snare",
    "Ajani Resolute",
    "Ajani, Caller of the Pride",
    "Ajani Unrelenting",
]

for c in cards:
    print(f"{c}: {pool.get(c, {}).get('qty', 'missing')}")
