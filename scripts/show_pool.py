import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

# Print all cards in the pool
print(f"Total cards in pool: {len(pool)}")
print("\nAll cards sorted:")
for name, data in sorted(pool.items()):
    print(f"  {name}: qty={data.get('qty', '?')}")
