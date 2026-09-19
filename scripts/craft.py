#!/usr/bin/env python3
"""Find high-value cards you do NOT own, ranked by how often they actually see play.

Uses Scryfall's edhrec_rank as the popularity signal (lower = played in more
decks). That ranking is built from 100-card singleton lists, so it maps well
onto Arena Brawl and is a far better "is this a staple?" proxy than guessing.

It is a weak signal for 60-card Standard, where inclusion is archetype-driven
rather than universal -- use it there only as a shortlist, not a verdict.

Examples:
    # Brawl staples missing from the collection, any colour
    python scripts/craft.py 'f:brawl'

    # only the colours you actually play
    python scripts/craft.py 'f:brawl id<=G'

    # cheap wins only
    python scripts/craft.py 'f:brawl r<=uncommon'

    # what you already own, to sanity-check the ranking
    python scripts/craft.py 'f:brawl' --owned
"""
import argparse
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "pool.json")

SEARCH = "https://api.scryfall.com/cards/search"
UA = "jerio-mtga-deckbuilding/1.0"


def norm(name):
    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


def utf8():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load_owned():
    if not os.path.exists(POOL):
        sys.exit("pool.json missing -- run scripts/pool.py first")
    pool = json.load(open(POOL, encoding="utf-8"))["pool"]
    owned = {}
    for name, e in pool.items():
        if e.get("qty", 0) > 0:
            owned[norm(name)] = e["qty"]
            owned.setdefault(norm(name.split(" // ")[0]), e["qty"])
    return owned


def search(query, pages):
    # Scryfall's "brawl: legal" says nothing about whether a card exists on
    # Arena -- Command Tower, Arcane Signet, Swords to Plowshares and Rhystic
    # Study are all brawl-legal and paper/MTGO only. Recommending those as
    # crafts is worse than useless, so every query is pinned to game:arena.
    if "game:arena" not in query:
        query = f"({query}) game:arena"
    # Arena's Brawl draws on the Historic card pool, so a card banned in
    # Historic is not safely craftable for Brawl even when Scryfall reports
    # brawl:legal -- Polluted Delta and Swords to Plowshares are both
    # historic:banned + brawl:legal. Require Historic legality too.
    if "f:brawl" in query and "f:historic" not in query:
        query = f"{query} f:historic"
    url = f"{SEARCH}?q={urllib.parse.quote(query)}&order=edhrec&unique=cards"
    seen = 0
    while url and seen < pages:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/json"}
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return
                if e.code == 429:
                    time.sleep(5 * (attempt + 1))
                    continue
                sys.exit(f"Scryfall HTTP {e.code}")
        else:
            sys.exit("Scryfall kept rate-limiting; wait a minute and retry.")
        yield from data.get("data", [])
        url = data.get("next_page")
        seen += 1
        time.sleep(0.12)


def main():
    utf8()
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", help="Scryfall query, e.g. 'f:brawl id<=G'")
    ap.add_argument("--owned", action="store_true",
                    help="invert: show high-value cards you DO own")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--pages", type=int, default=3,
                    help="Scryfall pages to scan (175 cards each)")
    args = ap.parse_args()

    owned = load_owned()
    rows = []
    for c in search(args.query, args.pages):
        have = owned.get(norm(c["name"]), 0)
        if bool(have) != args.owned:
            continue
        rows.append({
            "rank": c.get("edhrec_rank") or 999999,
            "name": c["name"],
            "cost": c.get("mana_cost") or "",
            "rarity": c.get("rarity", "?"),
            "ci": "".join(c.get("color_identity") or []) or "C",
            "type": (c.get("type_line") or "").split("—")[0].strip(),
            "have": have,
        })

    rows.sort(key=lambda r: r["rank"])
    verb = "own" if args.owned else "are MISSING"
    print(f"{len(rows)} card(s) you {verb}, ranked by play frequency\n")
    print(f"{'rank':>6}  {'cost':<13}{'name':<36}{'R':<3}{'CI':<4}type")
    for r in rows[:args.limit]:
        print(f"{r['rank']:>6}  {r['cost']:<13}{r['name'][:34]:<36}"
              f"{r['rarity'][:1].upper():<3}{r['ci']:<4}{r['type'][:22]}")
    if len(rows) > args.limit:
        print(f"\n... {len(rows) - args.limit} more (raise --limit)")


if __name__ == "__main__":
    main()
