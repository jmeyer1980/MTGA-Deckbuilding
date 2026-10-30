#!/usr/bin/env python3
import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

targets = [
    "Cooped Up", "Ferocity of the Hunt", "Fateful Discovery", "Ethereal Armor",
    "Prismatic Undercurrents", "Stasis Snare", "Assemble the Players", "Fated Firepower",
    "Revival of the Ancestors", "Ajani Resolute", "Ajani, Caller of the Pride",
    "Disenchant", "Annul", "Banishing Betrayal", "Repel Calamity", "Countersculpt",
    "Dawnwing Marshal", "Leonin Vanguard", "Felidar Savior", "Ajani's Pridemate",
    "Blossoming Sands", "Scoured Barrens", "Selesnya Guildgate", "Ojer Taq, Deepest Foundation",
]

for t in targets:
    matches = [k for k in pool if t.lower() in k.lower()]
    if matches:
        k = matches[0]
        info = pool[k]
        ci = info.get("color_identity", [])
        is_gw = set(ci) <= {"G", "W"}
        man = info.get("mana_cost", "?")
        print(f"{t:<55} qty={info.get('qty', 0):>3}  {info.get('type_line', '')[:60]}")
        print(f"{'':<55} man={man:<12} ci={ci} {'GW' if is_gw else 'NOT GW'}")
    else:
        print(f"{t:<55} NOT FOUND")
