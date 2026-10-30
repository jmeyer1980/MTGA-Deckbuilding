import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

# Search for all cards containing 'selesnya' or 'bloom' (G/W lands)
print("=== Selsnya/Bloom cards ===")
for name in sorted(pool.keys()):
    if 'selesnya' in name.lower() or 'bloom' in name.lower():
        print(f"  {name}: {pool[name]['qty']}")

# Count non-land G/W cards
print("\n=== All G/W cards (quick check) ===")
count = 0
for name in sorted(pool.keys()):
    # Colors G(3) W(5)
    if any(color in name.lower() for color in ['ajani', 'kutzil', 'banishing', 'leon', 'felidar', 'dawnwing', 'pridemate', 'selesnya', 'bloom']):
        print(f"  {name}: {pool[name]['qty']}")
        count += 1
print(f"Total: {count}")
