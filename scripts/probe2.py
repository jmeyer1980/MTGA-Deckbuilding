#!/usr/bin/env python3
import json
import urllib.request
UA = "jerio-mtga-deckbuilding/1.0"
tests = [
 "https://api.scryfall.com/cards/named?exact=Kutzil%2C+Malamet+Exemplar",
 "https://api.scryfall.com/cards/named?exact=Plains",
]
for URL in tests:
    print("URL:", URL)
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            card = json.load(r)
        print(" legalities:", json.dumps(card.get("legalities")))
    except Exception as e:
        print(" ERR:", e)
