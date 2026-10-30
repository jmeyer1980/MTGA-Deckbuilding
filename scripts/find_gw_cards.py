import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

# Search for G/W color cards by name
# These are G/W color-related cards
gw_search_terms = [
    "ajani", "kutzil", "banishing", "leon", "felidar", "dawnwing",
    "selesnya", "bloom", "pridemate", "ajani,", "ajani'", "ajani",
    "ajani's", "ajani", "ajani's", "ajani", "ajani's",
    "ajani", "ajani's"
]

# Also search for common G/W cards
all_gw = []
for name, data in sorted(pool.items()):
    name_lower = name.lower()
    # G/W color cards
    if any(kw in name_lower for kw in gw_search_terms):
        all_gw.append((name, data.get("qty", 0)))

print(f"Found {len(all_gw)} G/W cards in pool.json:")
for name, qty in all_gw:
    print(f"  {name}: qty={qty}")
