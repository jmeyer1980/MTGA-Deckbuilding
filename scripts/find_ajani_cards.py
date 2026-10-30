import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

# Find all cards that contain 'ajani' or 'ajani' case-insensitive
print("Cards with 'ajani' (case-insensitive):")
count = 0
for name in sorted(pool.keys()):
    if 'ajani' in name.lower():
        print(f"  {name}: qty={pool[name].get('qty', '?')}")
        count += 1

print(f"\nTotal: {count} cards")
