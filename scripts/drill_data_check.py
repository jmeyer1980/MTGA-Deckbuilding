"""Check pool.py fields + card cache fields for drill upgrade."""
import json
pool = json.load(open("pool.json", encoding="utf-8"))
p = pool.get("pool", pool)
k = "Hare Apparent"
print("pool keys sample:", list(p.keys())[:3])
print("Hare entry:", json.dumps(p.get(k), indent=2)[:2000])
print("Elspeth entry:", json.dumps(p.get("Elspeth, Storm Slayer"), indent=2)[:2000])
print("Nykthos entry:", json.dumps(p.get("Nykthos, Shrine to Nyx"), indent=2)[:2000])
try:
    cache = json.load(open(".card_cache.json", encoding="utf-8"))
    print("cache type:", type(cache))
    if isinstance(cache, dict):
        ks = list(cache.keys())[:3]
        print("cache keys:", ks)
        for kk in ks:
            print(kk, json.dumps(cache[kk], indent=2)[:1500])
    elif isinstance(cache, list):
        print("cache len", len(cache), json.dumps(cache[0], indent=2)[:1500])
except Exception as e:
    print("cache err:", e)
# pool.py source: what scryfall fields stored?
src = open("scripts/pool.py", encoding="utf-8").read()
print(src[:6000])
