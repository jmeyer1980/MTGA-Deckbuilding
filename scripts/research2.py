#!/usr/bin/env python3
import json, time, urllib.request, urllib.parse
ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
pool = json.load(open(ROOT + "/pool.json", encoding="utf-8"))["pool"]
def owned(n):
    e = pool.get(n); return e.get("qty", 0) if e else 0
API = "https://api.scryfall.com/cards/search"; UA = "jerio-mtga-deckbuilding/1.0"
def fetch(q, limit=40):
    out = []; url = f"{API}?{urllib.parse.urlencode({'q': q, 'unique': 'cards'})}"; pages = 0
    while url and len(out) < limit and pages < 6:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for c in data.get("data", []):
            if len(out) >= limit: break
            out.append(c)
        if not data.get("has_more") or len(out) >= limit: break
        url = data.get("next_page"); pages += 1; time.sleep(0.12)
    return out
def leg(c):
    l = c.get("legalities", {}); return l.get("competitivebrawl", "?")
def line(c):
    cb = leg(c); return f"[{cb}] {c['name']:<46} {c.get('mana_cost',''):<14} cmc={c.get('cmc')} {c.get('rarity'):<8} owned={owned(c['name'])}"
SECTIONS = {
    "C. PROTECTION (GW competitivebrawl)": '(o:"indestructible" OR o:"hexproof" OR o:"protection") id<=GW f:competitivebrawl -t:land',
    "D. TARGETED LAND REMOVAL (GW competitivebrawl)": 'o:"destroy target land" id<=GW f:competitivebrawl',
    "E. MASS LAND DENIAL (any color competitivebrawl)": 'o:"destroy all lands" OR o:"destroy each land" OR o:"all lands" f:competitivebrawl',
    "F. EXTRA TURNS (any color competitivebrawl)": 'o:"extra turn" f:competitivebrawl',
    "G. DOUBLERS / CRUSADE / COUNTER PAYOFFS": '"doubling season" OR "cathars crusade" OR "branching evolution" OR "primal vigor" OR "hardened scales" f:competitivebrawl',
    "H. ARTIFACT PAYOFFS": '"walking ballista" OR "hangarback walker" OR "animation module" OR "metallic mimic" OR "the ozolith" f:competitivebrawl',
}
for title, q in SECTIONS.items():
    print("\n" + "=" * 100)
    print(title); print(f"  q: {q}")
    cards = fetch(q, limit=40)
    if not cards:
        print("  (none found)"); continue
    cards.sort(key=lambda c: (-owned(c['name']), c.get('cmc', 99), c['name']))
    for c in cards:
        print("  ", line(c))
