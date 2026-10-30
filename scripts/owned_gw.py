#!/usr/bin/env python3
import json
pool = json.load(open("pool.json", encoding="utf-8"))["pool"]
owned = [(n, x) for n, x in pool.items()
         if x.get("qty", 0) >= 1
         and x.get("competitivebrawl") == "legal"
         and set(x.get("color_identity") or []) <= {"G", "W"}]
print("owned GW competitive-legal cards:", len(owned))
lands, walkers, creatures, enchant, artifacts, spells = [], [], [], [], [], []
for n, x in owned:
    t = x.get("type_line", "")
    if "Land" in t:
        lands.append((n, x))
    elif "Planeswalker" in t:
        walkers.append((n, x))
    elif "Creature" in t:
        creatures.append((n, x))
    elif "Enchantment" in t:
        enchant.append((n, x))
    elif "Artifact" in t:
        artifacts.append((n, x))
    else:
        spells.append((n, x))

def show(title, arr):
    print("\n%s (%d)" % (title, len(arr)))
    for n, x in sorted(arr):
        print("  %-42s %-8s qty=%s" % (n, x["rarity"], x["qty"]))

show("LANDS", lands)
show("PLANESWALKERS", walkers)
show("ARTIFACTS", artifacts)
show("ENCHANTMENTS", enchant)
show("CREATURES (1-drop/2-drop)", [c for c in creatures if c[1].get("cmc", 99) <= 2])
show("CREATURES (3-drop)", [c for c in creatures if c[1].get("cmc", 99) == 3])
show("CREATURES (4+ drop)", [c for c in creatures if c[1].get("cmc", 99) >= 4])
show("SPELLS", spells)
