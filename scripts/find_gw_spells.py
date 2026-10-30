#!/usr/bin/env python3
import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

# Find relevant cards in the pool for a Kutzil deck
# Categories: removal, counters, buffer creatures, ramp/lands

good_removals = []
good_counters = []
good_enchants = []

for n, x in pool.items():
    if x.get("standard") == "legal" and x.get("brawl") == "legal" and x.get("qty", 0) >= 1:
        t = x.get("type_line", "")
        if "Land" in t or "Creature" in t:
            continue
        name = n.lower()
        
        # Removal spells
        removal_terms = ["banish", "disenchant", "smite", "repel", "implode", "annul", "meddle", 
                        "halting", "intimidation", "undermine", "toll", "douse", "quench", "press",
                        "sublime", "sacrifice", "force"]
        if any(term in name for term in removal_terms):
            good_removals.append((n, t, x.get("qty", 0)))
        
        # Counter spells
        if "counter" in name:
            good_counters.append((n, t, x.get("qty", 0)))
        
        # Enchantments with positive effects
        if "enchantment" in t.lower():
            if any(term in name for term in ["banishing", "assembl", "cooped", "ethereal", 
                                              "ferocity", "fated", "fateful", "immolate", 
                                              "manifest", "prism", "reviv", "restor", 
                                              "sacrific", "shield", "stasis", "sublime",
                                              "summon", "symbios", "vigor", "wish"]):
                good_enchants.append((n, t, x.get("qty", 0)))

print("=== REMOVAL SPELLS ===")
for n, t, q in sorted(good_removals, key=lambda x: -x[2]):
    print(f"  {n:<55} qty={q}")

print("\n=== COUNTER SPELLS ===")
for n, t, q in sorted(good_counters, key=lambda x: -x[2]):
    print(f"  {n:<55} qty={q}")

print("\n=== ENCHANTMENTS (G/W friendly) ===")
for n, t, q in sorted(good_enchants, key=lambda x: -x[2]):
    print(f"  {n:<55} qty={q}")
