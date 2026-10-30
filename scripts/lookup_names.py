#!/usr/bin/env python3
import json, time, urllib.request, urllib.parse
ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
pool = json.load(open(ROOT + "/pool.json", encoding="utf-8"))["pool"]
def owned(n):
    e = pool.get(n); return e.get("qty", 0) if e else 0
API = "https://api.scryfall.com/cards/named?exact="; UA = "jerio-mtga-deckbuilding/1.0"
names = [
 "Craterhoof Behemoth","Avenger of Zendikar","Baneslayer Angel","Serra Avatar",
 "Archangel of Thune","Nissa, Who Shakes the World","Elspeth, Sun's Champion",
 "Ajani Goldmane","Gideon, Ally of Zendikar","Doubling Season","Branching Evolution",
 "Primal Vigor","Hangarback Walker","Animation Module","The Ozolith","Armageddon",
 "Fall of the Thran","Boseiju, Who Endures","Dust Bowl","Ghost Quarter",
 "Flawless Maneuver","Brave the Elements","Teferi's Protection","Eternal Witness",
 "Beast Within","Venerated Loxodon","Rishkar, Peema Renegade","Lifecrafter's Bestiary",
 "Sylvan Library","Gavony Township","Rampant Growth","Nature's Lore","Three Visits",
]
for n in names:
    url = API + urllib.parse.quote(n)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            c = json.load(r)
        l = c.get("legalities", {})
        cb = l.get('competitivebrawl', '?')
        tl = c.get('type_line', '')[:45]
        print(f"[{cb}] {c['name']:<40} {c.get('mana_cost',''):<13} cmc={c.get('cmc')} {c.get('rarity'):<8} owned={owned(c['name'])}  {tl}")
    except Exception as ex:
        print(f"[ERR] {n}: {ex}")
    time.sleep(0.12)
