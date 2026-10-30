import json

POOL = json.load(open("pool.json", encoding="utf-8"))["pool"]

# Cards with qty >= 2 in pool
multi = []
single = []
for name, data in POOL.items():
    if data.get("qty", 0) >= 2:
        multi.append(name)
    else:
        single.append(name)

print("Multi-copy cards (qty >= 2):")
for c in sorted(multi):
    print(f"  {c}: {POOL[c]['qty']}")

print("\nSingle-copy cards (qty == 1):")
for c in sorted(single):
    print(f"  {c}: {POOL[c]['qty']}")

print(f"\nTotal multi: {len(multi)}, total single: {len(single)}")
