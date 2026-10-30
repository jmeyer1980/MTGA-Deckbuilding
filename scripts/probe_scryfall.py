#!/usr/bin/env python3
"""Probe Scryfall card object for popularity/commander fields (Giada)."""

import json
import urllib.request

UA = "jerio-mtga-deckbuilding/1.0"
URL = "https://api.scryfall.com/cards/named?exact=Giada%2C+Font+of+Hope"

req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "application/json"})
with urllib.request.urlopen(req, timeout=30) as r:
    card = json.load(r)

print("Top-level keys:")
for k in sorted(card.keys()):
    print(f"  {k}")

print("\nPopularity fields:")
for k in ("edhrec_rank", "penny_rank", "prices", "related_uris", "games",
          "legalities", "arena_id", "cmc", "keywords", "rarity"):
    print(f"  {k} = {json.dumps(card.get(k))[:200]}")
