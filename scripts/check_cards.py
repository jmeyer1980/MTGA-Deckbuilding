#!/usr/bin/env python3
import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

key_cards = [
    "Blossoming Sands", "Scoured Barrens", "Selesnya Guildgate",
    "Ojer Taq, Deepest Foundation // Temple of Civilization",
    "Ajani's Pridemate", "Leonin Vanguard", "Dawnwing Marshal", "Felidar Savior",
    "Borosen, Winged Avenger", "Shieldmate", "Disenchant", "Mending",
    "Wall of Omens", "Glass Casket", "Counter Spike", "Unflinching Hortimancer",
    "Danitha, Sword of Hope", "Push", "Siphon Strike", "Reactivate Magic",
    "Agro", "Enchanted Wings", "Temple of Plenty", "Thalakos, the High Father",
    "Leyline of Sanctity",
]

for c in key_cards:
    matches = [k for k in pool if c.lower() in k.lower()]
    if matches:
        k = matches[0]
        print(f"{c:<55} qty={pool[k].get('qty', 0):>3} std={pool[k].get('standard', '?'):<8} brawl={pool[k].get('brawl', '?'):<8}")
    else:
        print(f"{c:<55} NOT FOUND")
