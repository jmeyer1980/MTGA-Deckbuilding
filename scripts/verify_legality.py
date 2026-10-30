#!/usr/bin/env python3
import json, time, urllib.request, urllib.parse
UA = 'jerio-mtga-deckbuilding/1.0'
for n in ["Cathars' Crusade", "Walking Ballista", "Craterhoof Behemoth", "Baneslayer Angel", "Archangel of Thune"]:
    url = 'https://api.scryfall.com/cards/named?exact=' + urllib.parse.quote(n)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=25) as r:
            c = json.load(r)
        l = c.get('legalities', {})
        print(f"{n:<30} competitivebrawl={l.get('competitivebrawl')} brawl={l.get('brawl')} standard={l.get('standard')} cmc={c.get('cmc')} rarity={c.get('rarity')}")
    except Exception as ex:
        print(f"{n}: ERR {ex}")
    time.sleep(0.15)
