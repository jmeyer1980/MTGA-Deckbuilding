#!/usr/bin/env python3
"""Validate an Arena deck file against format rules, the collection, and wildcards.

Checks construction legality (counts, singleton, colour identity), format
legality including bans, what the deck costs in wildcards, and the mana curve.

Formats:
    standard  60-card minimum, <=15 sideboard, max 4 copies, Standard-legal
    brawl     Arena's ranked 100-card Brawl: exactly 100 including the
              commander, singleton, colour identity enforced, no sideboard

Format is inferred from the filename ("brawl100-*" / "brawl-*" -> brawl,
anything else -> standard) unless --format is given.

Cards not in pool.json are looked up individually -- a deck may legitimately
contain cards you do not own yet; that is what the wildcard budget is for.

Usage:
    python scripts/deck_check.py decks/dimir-control.txt
    python scripts/deck_check.py decks/brawl100-gix-mono-black.txt
    python scripts/deck_check.py decks/*.txt --quiet
"""
import argparse
import glob
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "pool.json")
CACHE = os.path.join(ROOT, ".card_cache.json")
OVERRIDES = os.path.join(ROOT, "owned-overrides.txt")

UA = "jerio-mtga-deckbuilding/1.0"
NAMED = "https://api.scryfall.com/cards/named?exact="

BASICS = {
    "plains", "island", "swamp", "mountain", "forest", "wastes",
    "snow-covered plains", "snow-covered island", "snow-covered swamp",
    "snow-covered mountain", "snow-covered forest", "snow-covered wastes",
}

SECTION_RE = re.compile(r"^\s*(commander|deck|sideboard|companion)\s*$", re.I)
LINE_RE = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")
# Arena exports lines as "4 Deep-Cavern Bat (LCI) 102". The set code and
# collector number are printing info, not part of the name -- strip them or
# every lookup fails.
SET_SUFFIX_RE = re.compile(r"\s*\([A-Za-z0-9]{2,5}\)\s*\d*[a-z]?\s*$")
# Generic/variable pips that make cmc a lie about what the card really costs.
XCOST_RE = re.compile(r"\{X\}")

RARITY_ORDER = ("common", "uncommon", "rare", "mythic")


def norm(name):
    """Fold for matching: Arena strips diacritics, Scryfall keeps them."""
    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


class Cards:
    """Card lookup backed by pool.json, falling back to Scryfall."""

    def __init__(self):
        self.by_norm = {}
        if os.path.exists(POOL):
            pool = json.load(open(POOL, encoding="utf-8"))["pool"]
            for name, e in pool.items():
                rec = dict(e, name=name, owned=e.get("qty", 0))
                self.by_norm[norm(name)] = rec
                self.by_norm.setdefault(norm(name.split(" // ")[0]), rec)
        # Arena's export intermittently drops cards the player demonstrably
        # owns (Dollmaker's Shop has vanished and reappeared across exports).
        # owned-overrides.txt restores the confirmed count. Only the COUNT is
        # patched -- legality, rarity and type still come from the pool or a
        # live Scryfall lookup, so an override can never mask a real problem.
        self.overrides = {}
        if os.path.exists(OVERRIDES):
            for raw in open(OVERRIDES, encoding="utf-8"):
                line = raw.split("#", 1)[0].strip()
                if not line:
                    continue
                m = re.match(r"^(\d+)\s+(.+)$", line)
                if not m:
                    continue
                qty, name = int(m.group(1)), m.group(2).strip()
                self.overrides[norm(name)] = qty
                self.overrides.setdefault(norm(name.split(" // ")[0]), qty)
        for key, qty in self.overrides.items():
            rec = self.by_norm.get(key)
            if rec is not None:
                rec["owned"] = max(rec.get("owned", 0), qty)

        self.cache = {}
        if os.path.exists(CACHE):
            self.cache = json.load(open(CACHE, encoding="utf-8"))
        self.dirty = False

    def get(self, name):
        key = norm(name)
        if key in self.by_norm:
            return self.by_norm[key]
        if key in self.cache:
            # Cached lookups predate any override added since; re-apply the
            # confirmed count so a new owned-overrides.txt line takes effect
            # without deleting .card_cache.json.
            rec = self.cache[key]
            if key in self.overrides:
                rec["owned"] = max(rec.get("owned", 0), self.overrides[key])
            return rec

        url = NAMED + urllib.parse.quote(name)
        req = urllib.request.Request(
            url, headers={"User-Agent": UA, "Accept": "application/json"}
        )
        # A 429 is not a missing card. Retry it with backoff, and only treat a
        # genuine 404 as "no such card" -- otherwise rate limiting gets
        # misreported as an unresolvable name, which is a confidently wrong
        # answer about a card the player may well own.
        c = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    c = json.load(r)
                break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code == 429:
                    wait = 5 * (attempt + 1)
                    sys.stderr.write(
                        f"  rate-limited on {name!r}, waiting {wait}s\n"
                    )
                    time.sleep(wait)
                    continue
                raise
        if c is None:
            raise SystemExit(
                f"Scryfall kept rate-limiting on {name!r}. "
                "Wait a minute and re-run; this is not a missing card."
            )
        time.sleep(0.12)

        rec = {
            "name": c["name"],
            "mana_cost": c.get("mana_cost", ""),
            "cmc": c.get("cmc"),
            "rarity": c.get("rarity"),
            "type_line": c.get("type_line", ""),
            "color_identity": c.get("color_identity", []),
            "standard": c.get("legalities", {}).get("standard"),
            "brawl": c.get("legalities", {}).get("brawl"),
            "owned": 0,
            "any_number": any(
                "a deck can have any number of cards named" in (t or "").lower()
                for t in [c.get("oracle_text")]
                + [f.get("oracle_text") for f in c.get("card_faces") or []]
            ),
        }
        # A card absent from the export still gets its real count applied,
        # now that it carries full legality/rarity data from Scryfall.
        if key in self.overrides:
            rec["owned"] = max(rec.get("owned", 0), self.overrides[key])

        self.cache[key] = rec
        self.dirty = True
        return rec

    def save(self):
        if self.dirty:
            json.dump(self.cache, open(CACHE, "w", encoding="utf-8"), indent=1)


import urllib.parse  # noqa: E402  (needed by Cards.get)


def printed_mv(mana_cost):
    """Mana value read off the PRINTED cost, never from Scryfall's cmc.

    Counting pip groups undercounts generic mana -- {4}{G}{G} is three groups
    but costs six. Numerals contribute their value; every other symbol
    (coloured, hybrid, Phyrexian) counts as one. {X} contributes 0 and is
    reported separately, since its real floor depends on how it is cast.
    """
    total = 0
    for sym in re.findall(r"\{([^}]+)\}", mana_cost):
        if sym.isdigit():
            total += int(sym)
        elif sym.upper() in ("X", "Y", "Z"):
            continue
        else:
            total += 1
    return total


_WC_CACHE = {}


def wildcard_inventory():
    """Current wildcard counts from Player.log, or {} if unreadable.

    Reported as "?" rather than 0 when unavailable -- claiming zero wildcards
    would wrongly mark every deck unaffordable.
    """
    if _WC_CACHE:
        return _WC_CACHE
    try:
        sys.path.insert(0, HERE)
        import wildcards
        inv = wildcards.read_inventory(wildcards.DEFAULT_LOG)
        _WC_CACHE.update({r: inv[r] for r in RARITY_ORDER})
    except Exception:
        pass
    return _WC_CACHE


def unlimited(cards, name):
    """True for cards that opt out of the copy limit in their own rules text.

    Hare Apparent, Persistent Petitioners, Relentless Rats, Dragon's Approach
    and friends say "A deck can have any number of cards named ...". Treating
    them as singleton/4-of violations rejects perfectly legal decks.
    """
    c = cards.get(name)
    return bool(c and c.get("any_number"))


def parse_deck(path):
    sections = {"commander": [], "deck": [], "sideboard": [], "companion": []}
    current = "deck"
    for raw in open(path, encoding="utf-8"):
        if not raw.strip():
            continue
        m = SECTION_RE.match(raw)
        if m:
            current = m.group(1).lower()
            continue
        m = LINE_RE.match(raw)
        if m:
            name = SET_SUFFIX_RE.sub("", m.group(2)).strip()
            sections[current].append((int(m.group(1)), name))
    # Arena can list the same card on several lines (different printings).
    # Merge them, or a legitimate 4-of looks like four separate 1-ofs.
    for key, entries in sections.items():
        merged = {}
        for q, n in entries:
            merged[n] = merged.get(n, 0) + q
        sections[key] = [(q, n) for n, q in merged.items()]
    return sections


def infer_format(path):
    base = os.path.basename(path).lower()
    return "brawl" if base.startswith("brawl") else "standard"


def check(path, fmt, cards, quiet=False):
    sec = parse_deck(path)
    errors, warnings = [], []

    main = sec["deck"]
    cmdr = sec["commander"]
    side = sec["sideboard"]

    main_count = sum(q for q, _ in main)
    cmdr_count = sum(q for q, _ in cmdr)
    side_count = sum(q for q, _ in side)

    # ---- construction rules -------------------------------------------
    if fmt == "brawl":
        total = main_count + cmdr_count
        if cmdr_count != 1:
            errors.append(f"Brawl needs exactly 1 commander, found {cmdr_count}")
        if total != 100:
            errors.append(f"Brawl must be exactly 100 cards, found {total}")
        if side_count:
            errors.append(f"Brawl has no sideboard, found {side_count} cards")
        for q, n in main + cmdr:
            if q > 1 and norm(n) not in BASICS and not unlimited(cards, n):
                errors.append(f"Singleton violation: {q} x {n}")
    else:
        if main_count < 60:
            errors.append(f"Standard needs >=60 maindeck, found {main_count}")
        if side_count > 15:
            errors.append(f"Sideboard max 15, found {side_count}")
        if cmdr_count:
            warnings.append("Commander section ignored in Standard")
        totals = {}
        for q, n in main + side:
            totals[norm(n)] = totals.get(norm(n), 0) + q
        for n, q in totals.items():
            if q > 4 and n not in BASICS and not unlimited(cards, n):
                errors.append(f"More than 4 copies: {q} x {n}")

    # ---- per-card resolution ------------------------------------------
    entries = [(q, n, "commander") for q, n in cmdr]
    entries += [(q, n, "main") for q, n in main]
    entries += [(q, n, "side") for q, n in side]

    unresolved, illegal, banned = [], [], []
    shortfall = {r: 0 for r in RARITY_ORDER}
    shortfall_cards = []
    uncountable = []
    curve = {}
    xcards = []
    commander_ci = None

    for q, n, where in entries:
        c = cards.get(n)
        if c is None:
            unresolved.append(n)
            continue

        if where == "commander":
            commander_ci = set(c.get("color_identity") or [])
            tl = c.get("type_line", "")
            if "Legendary" not in tl or not (
                "Creature" in tl or "Planeswalker" in tl
            ):
                errors.append(f"Commander must be a legendary creature or planeswalker: {n} ({tl})")

        status = c.get(fmt)
        if status == "banned":
            banned.append(n)
        elif status not in ("legal", "restricted"):
            illegal.append(f"{n} ({status})")

        if norm(n) in BASICS:
            continue

        # Ownership -> wildcard cost. Arena grants basics freely.
        need = max(0, q - c.get("owned", 0))
        if need and c.get("any_number"):
            # Arena's collection export caps EVERY line at 4, including cards
            # you may legally own dozens of (Hare Apparent, Relentless Rats).
            # For these the owned count is a floor, not a fact, so charging
            # wildcards would confidently invent a cost that may not exist.
            uncountable.append((need, n))
        elif need:
            r = c.get("rarity") or "rare"
            r = r if r in shortfall else "rare"
            shortfall[r] += need
            shortfall_cards.append((need, n, r))

        mc = c.get("mana_cost") or ""
        if XCOST_RE.search(mc):
            xcards.append((n, mc))
        # Curve describes the MAINDECK you actually start with. Folding the
        # sideboard in inflates it -- boros-toys read as 52 spells for a
        # 37-spell deck.
        if where != "side" and "Land" not in (c.get("type_line") or ""):
            mv = printed_mv(mc)
            curve[mv] = curve.get(mv, 0) + q

    # ---- colour identity (Brawl) --------------------------------------
    if fmt == "brawl" and commander_ci is not None:
        for q, n, where in entries:
            if where == "commander":
                continue
            c = cards.get(n)
            if not c:
                continue
            ci = set(c.get("color_identity") or [])
            if not ci <= commander_ci:
                extra = "".join(sorted(ci - commander_ci))
                errors.append(f"Colour identity: {n} adds {{{extra}}} outside commander")

    # Affordability is decided here, before either reporting branch, so quiet
    # and full mode never disagree about whether a deck is buildable.
    have = wildcard_inventory()
    short_by = {
        r: shortfall[r] - have[r]
        for r in RARITY_ORDER
        if have.get(r) is not None and shortfall[r] > have[r]
    }
    if short_by:
        errors.append(
            "Not enough wildcards: "
            + ", ".join(f"{n} more {r}" for r, n in short_by.items())
        )

    if banned:
        errors.append(f"BANNED in {fmt}: " + ", ".join(sorted(set(banned))))
    if illegal:
        errors.append(f"Not legal in {fmt}: " + ", ".join(sorted(set(illegal))))
    if unresolved:
        errors.append("Unresolved card names: " + ", ".join(unresolved))

    # ---- report --------------------------------------------------------
    name = os.path.basename(path)
    ok = not errors
    if quiet:
        wc = " ".join(f"{r[0].upper()}{shortfall[r]}" for r in RARITY_ORDER if shortfall[r])
        print(f"{'OK  ' if ok else 'FAIL'}  {name:<40} {fmt:<9} "
              f"{main_count + cmdr_count:>3} cards  {wc or 'no wildcards needed'}")
        for e in errors:
            print(f"        - {e}")
        return ok

    print("=" * 68)
    print(f"{name}   [{fmt}]")
    print("=" * 68)
    if fmt == "brawl":
        print(f"Commander + deck : {main_count + cmdr_count}")
    else:
        print(f"Maindeck         : {main_count}")
        print(f"Sideboard        : {side_count}")

    print("\nCURVE (by printed mana value, lands excluded)")
    for p in sorted(curve):
        print(f"  {p}:  {'#' * curve[p]} ({curve[p]})")
    if xcards:
        print("\n  {X} COSTS -- cmc understates these, read the printed cost:")
        for n, mc in xcards:
            print(f"    {n:<40} {mc}")

    if uncountable:
        print("\nUNLIMITED-COPY CARDS (cost not computable)")
        for need, n in uncountable:
            print(f"    {n}: runs {need} more than the 4 the export reports")
        print("    Arena caps the collection export at 4 per line, so the true")
        print("    owned count is unknown. Check in Arena before crafting.")

    print("\nWILDCARD COST")
    if not any(shortfall.values()):
        print("  none -- every card is already in the collection")
    else:
        print(f"  {'rarity':<9} {'need':>5} {'have':>5}  {'after':>6}")
        for r in RARITY_ORDER:
            if shortfall[r]:
                h = have.get(r)
                left = "?" if h is None else h - shortfall[r]
                flag = "  SHORT" if (h is not None and left < 0) else ""
                print(f"  {r:<9} {shortfall[r]:>5} "
                      f"{'?' if h is None else h:>5}  {left:>6}{flag}")
        print()
        for need, n, r in sorted(shortfall_cards, key=lambda x: -x[0]):
            print(f"    {need} x {n:<38} ({r})")

    print()
    if ok:
        print("RESULT: legal and affordable")
    else:
        print(f"RESULT: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
    for w in warnings:
        print(f"  note: {w}")
    print()
    return ok


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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("decks", nargs="+")
    ap.add_argument("--format", choices=("standard", "brawl"))
    ap.add_argument("--quiet", action="store_true", help="one line per deck")
    args = ap.parse_args()

    paths = []
    for d in args.decks:
        paths.extend(sorted(glob.glob(d)) or [d])

    cards = Cards()
    allok = True
    for p in paths:
        if not os.path.exists(p):
            print(f"missing: {p}")
            allok = False
            continue
        fmt = args.format or infer_format(p)
        allok &= check(p, fmt, cards, quiet=args.quiet)
    cards.save()
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
