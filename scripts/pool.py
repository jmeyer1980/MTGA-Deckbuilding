#!/usr/bin/env python3
"""Build a legality-annotated card pool from collection.txt via Scryfall.

Reads collection.txt (lines of "<qty> <Card Name>"), sums duplicate name lines
(the same card appears once per set block in Arena's export), then batches
names to Scryfall's /cards/collection endpoint and caches the result to
pool.json.

Why this exists: checking legality by observing opponents' decks sees ROTATION
but never BANS -- a banned card simply never shows up. This pass catches both.

TRAPS encoded here:
  * mana_cost, not cmc. Scryfall reports Meathook Massacre II as cmc 4.0 when
    its real cost is {X}{X}{B}{B}{B}{B} -- a 6-mana floor. cmc is recorded but
    every consumer should read mana_cost.
  * WebFetch gets 403 from api.scryfall.com. Plain urllib works.
  * "A-" prefixed cards are Alchemy rebalances; they will not resolve by name
    and are reported separately, not treated as errors.

Usage:
    python scripts/pool.py                      # build/refresh pool.json
    python scripts/pool.py --report             # summarise legality + bans
    python scripts/pool.py --reuse --moxfield-csv  # export Moxfield CSV
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COLLECTION = os.path.join(ROOT, "collection.txt")
POOL = os.path.join(ROOT, "pool.json")

API = "https://api.scryfall.com/cards/collection"
UA = "jerio-mtga-deckbuilding/1.0"
BATCH = 75          # Scryfall hard limit per request
DELAY = 0.12        # Scryfall asks for 50-100ms between calls

LINE_RE = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


def norm(name):
    """Fold a card name for matching.

    TRAP: Arena's collection export strips diacritics ("Oin the Brave") while
    Scryfall returns them ("Oin the Brave" with the accent). Matching on the
    raw string silently yields qty 0 for every accented card -- the deck
    checker then rejects cards the player owns four copies of. Fold both
    sides before comparing.
    """
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()

# Fields we keep per card. Deliberately narrow -- pool.json stays readable.
KEEP = ("mana_cost", "cmc", "rarity", "type_line", "color_identity", "set", "oracle_text", "keywords", "produced_mana")

# Cards that opt out of the 4-of / singleton limit say so in their own text
# (Hare Apparent, Persistent Petitioners, Relentless Rats, Dragon's Approach...).
# We store the derived flag, not the full oracle text -- pool.json stays small.
ANY_NUMBER = "a deck can have any number of cards named"


def any_number(card):
    texts = [card.get("oracle_text") or ""]
    for face in card.get("card_faces") or []:
        texts.append(face.get("oracle_text") or "")
    return any(ANY_NUMBER in t.lower() for t in texts)


def parse_collection(path):
    """Return OrderedDict name -> total qty, summing duplicate lines."""
    counts = OrderedDict()
    bad = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            m = LINE_RE.match(raw)
            if not m:
                bad.append((lineno, raw.rstrip()))
                continue
            qty, name = int(m.group(1)), m.group(2)
            counts[name] = counts.get(name, 0) + qty
    return counts, bad


def post(names):
    body = json.dumps({"identifiers": [{"name": n} for n in names]}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            if attempt == 3:
                raise SystemExit(
                    "Scryfall kept rate-limiting a collection batch. "
                    "Wait a minute and re-run."
                ) from e
            wait = 5 * (attempt + 1)
            sys.stderr.write(f"  rate-limited on collection batch, waiting {wait}s\n")
            time.sleep(wait)


def build(counts):
    names = list(counts)
    pool, missing = {}, []

    # Folded lookup: handles diacritics and the front-face-only names Arena
    # writes for double-faced / Adventure cards ("Glóin the Mighty" in the
    # export vs "Glóin the Mighty // Easy Pickings" from Scryfall).
    folded = {norm(n): q for n, q in counts.items()}

    def qty_for(card_name):
        key = norm(card_name)
        if key in folded:
            return folded[key]
        return folded.get(norm(card_name.split(" // ")[0]), 0)

    for i in range(0, len(names), BATCH):
        chunk = names[i:i + BATCH]
        try:
            data = post(chunk)
        except urllib.error.HTTPError as e:
            sys.exit(f"Scryfall HTTP {e.code} on batch {i//BATCH + 1}: {e.read()[:300]}")

        for card in data.get("data", []):
            entry = {k: card.get(k) for k in KEEP}
            entry["qty"] = qty_for(card["name"])
            entry["any_number"] = any_number(card)
            leg = card.get("legalities", {})
            # 'brawl' is CASUAL 100-card Brawl's list; 'competitivebrawl' is
            # the ranked ladder (commanders-only bans). 'standardbrawl' is
            # the 60-card singleton format with its own (more restrictive)
            # ban list -- stored explicitly so Standard Brawl checks ban
            # against the right list, not Standard's. Fallback keeps a
            # Scryfall schema gap from becoming a missing key.
            entry["standard"] = leg.get("standard")
            entry["standardbrawl"] = leg.get("standardbrawl")
            entry["brawl"] = leg.get("brawl")
            entry["competitivebrawl"] = (
                leg.get("competitivebrawl") or leg.get("brawl")
            )
            pool[card["name"]] = entry

        for nf in data.get("not_found", []):
            missing.append(nf.get("name", "?"))

        sys.stderr.write(f"\r  resolved {min(i+BATCH, len(names))}/{len(names)}")
        sys.stderr.flush()
        time.sleep(DELAY)

    sys.stderr.write("\n")

    # Reconcile: every copy in collection.txt must land somewhere in the pool.
    # A silent shortfall means names failed to match and cards will look
    # unowned. Surface it loudly rather than shipping a quietly wrong pool.
    want = sum(counts.values())
    got = sum(e["qty"] for e in pool.values())
    if got != want:
        placed = {norm(n) for n in pool}
        placed |= {norm(n.split(" // ")[0]) for n in pool}
        orphans = [(n, q) for n, q in counts.items() if norm(n) not in placed]
        sys.stderr.write(
            f"\nRECONCILE MISMATCH: collection has {want} copies, "
            f"pool accounts for {got} (delta {want - got}).\n"
        )
        for n, q in orphans[:20]:
            sys.stderr.write(f"    unplaced: {q} x {n}\n")
        if len(orphans) > 20:
            sys.stderr.write(f"    ... and {len(orphans) - 20} more\n")

    return pool, missing


def report(pool, missing):
    total = sum(e["qty"] for e in pool.values())
    std_legal = [n for n, e in pool.items() if e["standard"] == "legal"]
    std_banned = [n for n, e in pool.items() if e["standard"] == "banned"]
    brawl_legal = [n for n, e in pool.items() if e["brawl"] == "legal"]
    brawl_banned = [n for n, e in pool.items() if e["brawl"] == "banned"]
    comp_brawl_banned = [
        n for n, e in pool.items() if e.get("competitivebrawl") == "banned"
    ]

    print(f"Distinct resolved : {len(pool)}")
    print(f"Total copies      : {total}")
    print()
    print(f"Standard legal    : {len(std_legal)}")
    print(f"Standard BANNED   : {len(std_banned)}")
    for n in sorted(std_banned):
        print(f"    ! {n}")
    print()
    print(f"Brawl legal       : {len(brawl_legal)}")
    print(f"Casual Brawl BANNED: {len(brawl_banned)}")
    for n in sorted(brawl_banned):
        print(f"    ! {n}")
    print()
    print(f"Competitive (ranked) Brawl BANNED: {len(comp_brawl_banned)}")
    for n in sorted(comp_brawl_banned):
        print(f"    ! {n}")

    alchemy = [n for n in missing if n.startswith("A-")]
    other = [n for n in missing if not n.startswith("A-")]
    print()
    print(f"Alchemy rebalances (expected, not errors): {len(alchemy)}")
    if other:
        print(f"Unresolved names ({len(other)}):")
        for n in sorted(other)[:40]:
            print(f"    ? {n}")
        if len(other) > 40:
            print(f"    ... and {len(other)-40} more")


def write_moxfield_csv(pool, path):
    """Write owned quantities in Moxfield's supported Count/Name CSV format."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    total = 0
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(("Count", "Name"))
        for name, entry in sorted(pool.items(), key=lambda item: item[0].casefold()):
            qty = entry.get("qty", 0)
            if qty > 0:
                writer.writerow((qty, name))
                total += qty
    print(f"Wrote {path} ({total} copies)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collection", default=COLLECTION)
    ap.add_argument("--out", default=POOL)
    ap.add_argument("--moxfield-csv", nargs="?",
                    const=os.path.join(ROOT, "collection-moxfield.csv"),
                    metavar="PATH",
                    help="also write a Moxfield Count/Name CSV "
                         "(default: collection-moxfield.csv)")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--reuse", action="store_true",
                    help="report from existing pool.json without re-fetching")
    args = ap.parse_args()

    if args.reuse:
        with open(args.out, encoding="utf-8") as fh:
            saved = json.load(fh)
        if args.moxfield_csv:
            write_moxfield_csv(saved["pool"], args.moxfield_csv)
        report(saved["pool"], saved["missing"])
        return

    if not os.path.exists(args.collection):
        sys.exit(f"collection.txt not found at {args.collection}")

    counts, bad = parse_collection(args.collection)
    if bad:
        print(f"WARNING: {len(bad)} unparseable lines (first 5):", file=sys.stderr)
        for lineno, raw in bad[:5]:
            print(f"  line {lineno}: {raw!r}", file=sys.stderr)

    print(f"Parsed {len(counts)} distinct names "
          f"({sum(counts.values())} copies) from collection.txt", file=sys.stderr)

    pool, missing = build(counts)

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"pool": pool, "missing": missing}, fh, indent=1)
    print(f"Wrote {args.out}", file=sys.stderr)

    if args.moxfield_csv:
        write_moxfield_csv(pool, args.moxfield_csv)

    if args.report:
        print()
        report(pool, missing)


if __name__ == "__main__":
    main()
