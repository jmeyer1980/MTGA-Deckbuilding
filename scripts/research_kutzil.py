#!/usr/bin/env python3
"""Research competitive Brawl-legal GW cards for a Kutzil +1/+1 counter deck."""
import json, time, urllib.request, urllib.parse

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
API = "https://api.scryfall.com/cards/search"
UA = "jerio-mtga-deckbuilding/1.0"

pool = json.load(open(POOL, encoding="utf-8"))["pool"]
def owned(name):
    e = pool.get(name)
    return e.get("qty", 0) if e else 0

def fetch(q, limit=60):
    out = []
    url = f"{API}?{urllib.parse.urlencode({'q': q, 'unique': 'cards'})}"
    pages = 0
    while url and len(out) < limit and pages < 6:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for c in data.get("data", []):
            if len(out) >= limit:
                break
            out.append(c)
        if not data.get("has_more") or len(out) >= limit:
            break
        url = data.get("next_page")
        pages += 1
        time.sleep(0.12)
    return out

def leg(c):
    l = c.get("legalities", {})
    return l.get("competitivebrawl", "?"), l.get("brawl", "?"), l.get("standard", "?")

def line(c):
    cb, b, std = leg(c)
    return f"[{cb}] {c['name']:<44} {c.get('mana_cost',''):<13} cmc={c.get('cmc')} {c.get('rarity'):<8} owned={owned(c['name'])}"

print("=" * 100)
print("KUTZIL ORACLE TEXT")
k = fetch('!"Kutzil, Malamet Exemplar"', limit=1)[0]
print(f"  {k['mana_cost']}  {k['type_line']}")
print(f"  {k.get('oracle_text','')}")
print(f"  legalities: competitivebrawl={leg(k)[0]}, standard={leg(k)[2]}")

SECTIONS = {
    "A. +1/+1 COUNTER SYNERGY (GW, competitivebrawl)": 'o:"+1/+1 counter" id<=GW f:competitivebrawl -t:land',
    "B. ATTACK TRIGGERS / GO-WIDE (GW, competitivebrawl)": 'o:"whenever you attack" id<=GW f:competitivebrawl -t:land',
    "C. PROTECTION / INDSTRUCTIBLE / HEXPROOF (GW)": '(o:"indestructible" o:creature OR o:"hexproof" o:creature) id<=GW f:competitivebrawl -t:land',
    "D. TARGETED LAND REMOVAL (GW competitivebrawl)": 'o:"destroy target land" id<=GW f:competitivebrawl',
    "E. MASS LAND DENIAL (any color, competitivebrawl)": 'o:"destroy all lands" OR o:"destroy each land" f:competitivebrawl',
    "F. EXTRA TURNS (any color, competitivebrawl)": 'o:"extra turn" f:competitivebrawl',
    "G. COUNTER DOUBLERS / CRUSADE": '"doubling season" OR "cathars crusade" OR "branching evolution" OR "primal vigor" f:competitivebrawl',
    "H. ARTIFACT COUNTER PAYOFFS": '"walking ballista" OR "hangarback walker" OR "animation module" OR "the ozolith" f:competitivebrawl',
    "I. PLANESWALKER HAYMAKERS (GW)": 't:planeswalker id<=GW f:competitivebrawl',
    "J. BIG THREATS (GW competitivebrawl, cmc>=5)": 'id<=GW f:competitivebrawl -t:land cmc>=5',
}

for title, q in SECTIONS.items():
    print("\n" + "=" * 100)
    print(title)
    print(f"  scryfall q: {q}")
    cards = fetch(q, limit=40)
    if not cards:
        print("  (none found)")
        continue
    cards.sort(key=lambda c: (-owned(c['name']), c.get('cmc', 99), c['name']))
    for c in cards[:24]:
        print("  ", line(c))
    if len(cards) > 24:
        print(f"  ... ({len(cards)-24} more)")
