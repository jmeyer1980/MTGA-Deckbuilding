import json
pool = json.load(open('pool.json', encoding='utf-8'))['pool']
for n in ["Cathars' Crusade", "Craterhoof Behemoth", "Baneslayer Angel", "Archangel of Thune"]:
    e = pool.get(n)
    q = e.get('qty', 0) if e else 0
    print(f"{n:<32} qty={q} rarity={e.get('rarity') if e else 'N/A'} cb={e.get('competitivebrawl') if e else 'N/A'}")
