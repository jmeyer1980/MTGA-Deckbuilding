#!/usr/bin/env python3
import urllib.parse, urllib.request, json
UA='jerio-mtga-deckbuilding/1.0'
for name in ["Kutzil, Malamet Exemplar", "Blossoming Sands", "Ajani's Welcome"]:
    url='https://api.scryfall.com/cards/named?exact='+urllib.parse.quote(name, safe='')
    req=urllib.request.Request(url, headers={'User-Agent':UA, 'Accept':'application/json'})
    try:
        c=json.load(urllib.request.urlopen(req, timeout=20))
        print("==", name)
        print(" keys:", sorted(c.get('legalities',{}).keys()))
        import pprint
        pprint.pprint(c.get('legalities'))
        print(" CI:", c.get('color_identity'), "type:", c.get('type_line'))
    except Exception as e:
        print("FAIL", name, e)
    import time; time.sleep(0.15)
