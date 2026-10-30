#!/usr/bin/env python3
import json, urllib.request, urllib.parse, time
UA='jerio-mtga-deckbuilding/1.0'
def get(n):
    url='https://api.scryfall.com/cards/named?exact='+urllib.parse.quote(n)
    req=urllib.request.Request(url, headers={'User-Agent':UA})
    c=json.load(urllib.request.urlopen(req))
    return c
for n in ['Plains','Kutzil, Malamet Exemplar',"Ajani's Welcome",'Blossoming Sands']:
    c=get(n)
    print('===',c['name'],'===')
    print(json.dumps(c.get('legalities'), indent=1))
    time.sleep(0.15)
