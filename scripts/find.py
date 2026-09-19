#!/usr/bin/env python3
"""Search Scryfall and intersect the results with the collection.

The build pipeline says "pick a shell, then fill from the pool" -- this is how
you search the pool by effect rather than by name. Any Scryfall query syntax
works; results are filtered to cards actually owned unless --all is passed.

Examples:
    # mono-black token generators you own, legal in Brawl
    python scripts/find.py 'id<=B f:brawl o:"creature token"'

    # cheap green ramp for a mono-green commander
    python scripts/find.py 'id<=G f:brawl o:"add" mv<=3 -t:land'

    # what Standard-legal removal do I have?
    python scripts/find.py 'f:standard o:"destroy target creature"'

    # include cards you do NOT own, to price them in wildcards
    python scripts/find.py 'id<=B f:brawl t:"legendary creature"' --all

Sort defaults to mana value. Use --sort name|rarity to change it.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "pool.json")

SEARCH = "https://api.scryfall.com/cards/search"
UA = "jerio-mtga-deckbuilding/1.0"

RARITY_RANK = {"common": 0, "uncommon": 1, "rare": 2, "mythic": 3}


def norm(name):
    import unicodedata
    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


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


def search(query):
    """Yield every card matching the query, following pagination."""
    url = f"{SEARCH}?q={urllib.parse.quote(query)}&unique=cards"
    while url:
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return  # Scryfall returns 404 for "no cards matched"
            sys.exit(f"Scryfall HTTP {e.code}: {e.read()[:300]}")
        yield from data.get("data", [])
        url = data.get("next_page")
        time.sleep(0.12)


def oracle(card):
    t = card.get("oracle_text")
    if t:
        return t
    return " // ".join(
        f.get("oracle_text", "") for f in card.get("card_faces") or []
    )


def _utf8_stdout():
    """Windows consoles default to cp1252 and card text is full of Unicode
    (the real minus sign in "-1/-1", accented names). Without this, printing a
    result set crashes instead of showing it."""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    _utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", help="Scryfall search query")
    ap.add_argument("--all", action="store_true",
                    help="include cards not in the collection")
    ap.add_argument("--sort", choices=("mv", "name", "rarity"), default="mv")
    ap.add_argument("--text", action="store_true", help="show full oracle text")
    ap.add_argument("--limit", type=int, default=80)
    args = ap.parse_args()

    owned = load_owned()
    rows = []
    for c in search(args.query):
        have = owned.get(norm(c["name"]), 0)
        if not have and not args.all:
            continue
        rows.append({
            "have": have,
            "name": c["name"],
            "cost": c.get("mana_cost") or "",
            "mv": c.get("cmc") or 0,
            "rarity": c.get("rarity", "?"),
            "type": c.get("type_line", ""),
            "text": oracle(c).replace("\n", " / "),
            "arena": None,   # filled in below by an authoritative pass
        })

    # Arena availability, done right. A card's `games` field describes ONE
    # printing, so reading it mislabels cards whose Arena release differs from
    # their default printing (Swords to Plowshares, Command Tower, Arcane
    # Signet all read paper-only that way, and all three are on Arena).
    # Re-running the same query under `game:arena` is authoritative because
    # Scryfall applies it across every printing.
    if args.all and rows:
        on_arena = {norm(c["name"]) for c in search(f"({args.query}) game:arena")}
        for r in rows:
            r["arena"] = norm(r["name"]) in on_arena
    else:
        for r in rows:
            r["arena"] = True     # owned cards are on Arena by definition

    key = {
        "mv": lambda r: (r["mv"], r["name"]),
        "name": lambda r: r["name"],
        "rarity": lambda r: (RARITY_RANK.get(r["rarity"], 9), r["mv"]),
    }[args.sort]
    rows.sort(key=key)

    print(f"{len(rows)} result(s)"
          f"{'' if args.all else ' owned'} for: {args.query}\n")
    for r in rows[:args.limit]:
        mark = f"{r['have']}x" if r["have"] else " -"
        flag = "" if r["arena"] else "   [NOT ON ARENA]"
        print(f"{mark:>3} {r['cost']:<14} {r['name'][:38]:<38} "
              f"{r['rarity'][:1].upper()}  {r['type'][:26]}{flag}")
        if args.text:
            print(f"        {r['text'][:200]}")
    if len(rows) > args.limit:
        print(f"\n... {len(rows) - args.limit} more (raise --limit)")


if __name__ == "__main__":
    main()
