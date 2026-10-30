#!/usr/bin/env python3
"""Build the Kutzil Standard Brawl (60) and Competitive Brawl (100) decks.

Rules enforced here (all confirmed with the pilot):
  * Singleton: every unique card name exactly once. Only basic lands (and
    any-number cards) may repeat -- basics are UNLIMITED, not capped at 4.
  * Kutzil, Malamet Exemplar is the commander in both decks.
  * Colour identity = Kutzil's {G,W}: every card's CI must be a SUBSET of
    {G,W} -- colourless, mono-W, mono-G and GW gold cards all qualify.
    (The pilot's "62 cards with GW identity" was the gold-only slice; the
    deck may use the full subset.)
  * 60-card deck: commander + 59, every card legal in `standardbrawl`
    (Scryfall's Standard Brawl legality -- its own, more restrictive ban
    list, NOT plain Standard).
  * 100-card deck: commander + 99, every card legal in `competitivebrawl`
    (Arena ranked Brawl's list).

Card selection is data-driven: oracle text is fetched from Scryfall and
scored for Kutzil's game plan (creatures that attack, +1/+1 counters,
anthems, cheap interaction). No card is hand-waved from memory.

Usage:
    python scripts/build_kutzil_decks.py
"""
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "pool.json")
DECKS = os.path.join(ROOT, "decks")

API = "https://api.scryfall.com/cards/collection"
UA = "jerio-mtga-deckbuilding/1.0"
BATCH = 75
DELAY = 0.12

COMMANDER = "Kutzil, Malamet Exemplar"
OUT_60 = os.path.join(DECKS, "standard60-brawl-kutzil.txt")
OUT_100 = os.path.join(DECKS, "brawl100-kutzil.txt")

# Kutzil wants two attackers and pays you with cards; +1/+1 counters give
# her whole board hexproof. Score every line of oracle text against that.
POS = (
    ("+1/+1 counter", 4),
    ("counters onto", 1),
    ("whenever you attack", 5),
    ("whenever ~ attacks", 4),
    ("whenever this creature attacks", 4),
    ("creatures you control get +", 4),
    ("creatures you control have", 3),
    ("creatures you control gain", 3),
    ("creature you control gets +", 3),
    ("gets +1/+1", 2),
    ("vigilance", 2),
    ("trample", 1),
    ("hexproof", 2),
    ("indestructible", 2),
    ("draw a card", 2),
    ("draw cards", 2),
    ("destroy target creature", 3),
    ("exile target creature", 3),
    ("destroy target", 2),
    ("exile target", 2),
    ("damage to any target", 2),
    ("damage to target", 2),
    ("can't be blocked", 2),
    ("must be blocked", 1),
    ("enters the battlefield", 1),
    ("enters tapped", -2),
    ("you lose", -4),
    ("pay ", -1),
)
NEG_TEXT = (
    ("can't attack", -4),
    ("cannot attack", -4),
    ("defender", -4),
    ("defenders", -4),
)


def norm(name):
    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


def front(name):
    """Arena writes only the front face of DFC/Adventure cards."""
    return name.split(" // ")[0]


def post(names):
    body = json.dumps({"identifiers": [{"name": n} for n in names]}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"User-Agent": UA, "Accept": "application/json",
                 "Content-Type": "application/json"},
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise SystemExit("Scryfall kept rate-limiting. Wait a minute and re-run.")


def text_of(card):
    parts = [card.get("oracle_text") or ""]
    for f in card.get("card_faces") or []:
        parts.append(f.get("oracle_text") or "")
    return "\n".join(parts).lower()


def score_card(text, mv, is_creature):
    s = 0.0
    for frag, w in POS:
        s += text.count(frag) * w
    for frag, w in NEG_TEXT:
        s += text.count(frag) * w
    # Kutzil curves out at 3 (herself); bodies beat effects past that.
    if is_creature:
        s += {0: 2, 1: 5, 2: 4.5, 3: 4, 4: 2, 5: 0, 6: -2}.get(int(mv), -3)
    else:
        s += {0: 0, 1: 3, 2: 2, 3: 1, 4: 0}.get(int(mv), -2)
    return s


def fetch_text(names):
    """oracle_text for every candidate name, batched through Scryfall."""
    out = {}
    names = list(names)
    for i in range(0, len(names), BATCH):
        chunk = names[i:i + BATCH]
        data = post(chunk)
        for card in data.get("data", []):
            out[card["name"]] = text_of(card)
        for nf in data.get("not_found", []):
            sys.stderr.write(f"  not found: {nf.get('name')}\n")
        sys.stderr.write(f"\r  text {min(i + BATCH, len(names))}/{len(names)}")
        sys.stderr.flush()
        time.sleep(DELAY)
    sys.stderr.write("\n")
    return out


def pick_lands(land_pool, text, want_util):
    """All owned GW-fixing duals, then the best `want_util` utility lands.

    Basics are appended by the caller -- Arena grants them freely and
    Brawl caps nothing about their count.
    """
    duals, utility = [], []
    for name, e in land_pool:
        t = text.get(name) or ""
        tl = e.get("type_line") or ""
        is_fixer = "Gate" in tl or "Forest Plains" in tl
        if is_fixer:
            duals.append(name)
            continue
        s = 0.0
        for frag, w in (("can't be blocked", 6), ("search your library", 3),
                        ("scry", 2), ("draw a card", 3), ("+1/+1", 2),
                        ("add {g}{w}", 2), ("add one mana", 1)):
            s += t.count(frag) * w
        if s > 0:
            utility.append((s, name))
    utility.sort(key=lambda x: (-x[0], x[1]))
    util_names = [n for _, n in utility[:want_util]]
    return duals + util_names


def build(out_path, legality_key, want_total, n_util, basics_w, basics_g):
    pool = json.load(open(POOL, encoding="utf-8"))["pool"]

    # Candidate pool: owned, CI subset of Kutzil's {G,W}, format-legal,
    # not the commander (it lives in the Commander section).
    cand = []
    land_pool = []
    for name, e in pool.items():
        if norm(name) == norm(COMMANDER):
            continue
        if not e.get("qty"):
            continue
        if e.get(legality_key) != "legal":
            continue
        if not set(e.get("color_identity") or []) <= {"G", "W"}:
            continue
        tl = e.get("type_line") or ""
        if "Land" in tl:
            land_pool.append((name, e))
        else:
            cand.append((name, e))
    sys.stderr.write(f"  nonland candidates ({legality_key}): {len(cand)}\n")
    sys.stderr.write(f"  land candidates ({legality_key}): {len(land_pool)}\n")

    text = fetch_text(n for n, _ in cand + land_pool)

    # Score nonlands; split into creatures (Kutzil needs attackers) and
    # everything else (interaction, anthems, auras).
    scored = []
    for name, e in cand:
        tl = e.get("type_line") or ""
        is_creature = "Creature" in tl
        mv = int(e.get("cmc") or 0)
        scored.append((score_card(text.get(name) or "", mv, is_creature),
                       mv, name, is_creature))
    scored.sort(key=lambda x: (-x[0], x[1], x[2]))

    land_names = pick_lands(land_pool, text, n_util)
    n_land = len(land_names) + basics_w + basics_g
    n_spell = want_total - 1 - n_land  # -1 for the commander
    n_crea = max(1, round(n_spell * 0.72))
    n_oth = n_spell - n_crea

    creas_picked = [(mv, n) for s, mv, n, c in scored if c][:n_crea]
    others_picked = [(mv, n) for s, mv, n, c in scored if not c][:n_oth]

    if len(creas_picked) < n_crea or len(others_picked) < n_oth:
        sys.exit(f"ERROR: not enough owned {legality_key}-legal Selesnya "
                 f"cards. Need {n_crea}+{n_oth}, have "
                 f"{len(creas_picked)}+{len(others_picked)}.")

    spells_sorted = sorted(creas_picked + others_picked, key=lambda x: x[1])

    lines = ["Commander", f"1 {COMMANDER}", "", "Deck"]
    for _, n in spells_sorted:
        lines.append(f"1 {front(n)}")
    for n in land_names:
        lines.append(f"1 {front(n)}")
    if basics_w:
        lines.append(f"{basics_w} Plains")
    if basics_g:
        lines.append(f"{basics_g} Forest")

    total = 1 + len(spells_sorted) + len(land_names) + basics_w + basics_g
    assert total == want_total, f"{out_path}: built {total}, wanted {want_total}"
    # Singleton audit -- the rule the pilot has corrected repeatedly.
    seen = {}
    for ln in lines:
        if ln and ln[0].isdigit():
            q, n = ln.split(" ", 1)
            if n not in ("Plains", "Forest"):
                seen[n] = seen.get(n, 0) + int(q)
    dups = {n: q for n, q in seen.items() if q > 1}
    if dups:
        sys.exit(f"ERROR: duplicate singleton cards in {out_path}: {dups}")

    os.makedirs(DECKS, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    sys.stderr.write(
        f"  wrote {out_path}: {total} = 1 cmdr + {len(spells_sorted)} spells "
        f"({len(creas_picked)} creatures) + {len(land_names)} nonbasic + "
        f"{basics_w} Plains + {basics_g} Forest\n"
    )


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("=== Standard Brawl (60: commander + 59) ===")
    # 59 = 24 lands (10 duals + 4 utility + 10 basics) + 35 spells
    build(OUT_60, "standardbrawl", 60,
          n_util=4, basics_w=5, basics_g=5)
    print("=== Competitive Brawl (100: commander + 99) ===")
    # 99 = 36 lands (12 duals + 8 utility + 16 basics) + 63 spells
    build(OUT_100, "competitivebrawl", 100,
          n_util=8, basics_w=8, basics_g=8)


if __name__ == "__main__":
    main()
