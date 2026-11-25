#!/usr/bin/env python3
"""Oracle-enriched pool builder with functional tagging and synergy features.

Extends pool.json with full Scryfall data (oracle_text, keywords, type_line,
produced_mana, legalities, card_faces) and deterministically tags every card
with functional roles plus synergy features.

Usage:
    python scripts/pool_enricher.py              # rebuild enriched pool from pool.json
    python scripts/pool_enricher.py --report      # show tag distribution
    python scripts/pool_enricher.py --reuse       # report from existing enriched file

Enriched output: scripts/enriched_pool.json  (pool.json stays untouched for
backward compatibility with deck_check.py and other consumers).

Preserves pool.py's 429 rate-limit backoff for any live Scryfall lookups.
"""
import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from math import log

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = os.path.join(ROOT, "pool.json")
ENRICHED = os.path.join(ROOT, "scripts", "enriched_pool.json")

UA = "jerio-mtga-deckbuilding-enricher/1.0"
NAMED = "https://api.scryfall.com/cards/named?exact="
DELAY = 0.12

# ---------------------------------------------------------------------------
# Functional role keywords (rule-based, derived from Oracle text + type_line)
# Each role maps to a list of (pattern, weight) tuples. Higher weight = stronger
# signal. Patterns are matched case-insensitively against folded oracle text
# and type_line.
# ---------------------------------------------------------------------------

ROLE_PATTERNS = {
    "ramp": [
        (r"\bsearch your library for a (basic )?land\b", 3),
        (r"\bput .* land .* battlefield\b", 3),
        (r"\badd .* mana\b", 2),
        (r"\bmana\b.*\badd\b", 2),
        (r"\bramp\b", 3),
        (r"\bexplore\b", 1),
        (r"\bdark ritual\b", 3),
        (r"\bseething song\b", 3),
        (r"\bcultivate\b", 3),
        (r"\bkodama's reach\b", 3),
        (r"\bnature's lore\b", 3),
        (r"\brampant growth\b", 3),
        (r"\bfarseek\b", 3),
        (r"\bnature's way\b", 2),
        (r"\bwild growth\b", 3),
        (r"\butopia\b", 2),
        (r"\bllanowar elves\b", 3),
        (r"\bbirds of paradise\b", 3),
        (r"\bmana dork\b", 2),
        (r"\bmana rock\b", 2),
        (r"\bsignet\b", 2),
        (r"\btalisman\b", 2),
        (r"\bmana vault\b", 3),
        (r"\bsol ring\b", 3),
        (r"\bmana crypt\b", 3),
    ],
    "spot_removal": [
        (r"\bdestroy target\b", 3),
        (r"\bexile target\b", 3),
        (r"\b-1/-1\b.*\buntil end of turn\b", 2),
        (r"\bdeals? \d+ damage to(?: any)? target\b", 2),
        (r"\bpath to exile\b", 3),
        (r"\bswords to plowshares\b", 3),
        (r"\bmurder\b", 3),
        (r"\bdestroy target creature\b", 3),
        (r"\bexile target creature\b", 3),
        (r"\bconditional destruction\b", 1),
    ],
    "board_wipe": [
        (r"\bdestroy all\b", 3),
        (r"\bexile all\b", 3),
        (r"\bwipe\b", 2),
        (r"\bwrath\b", 3),
        (r"\bday of judgment\b", 3),
        (r"\bdamnation\b", 3),
        (r"\bblasphemous act\b", 3),
        (r"\bcyclonic rift\b", 3),
        (r"\bcleanse\b", 2),
        (r"\bobliterate\b", 3),
        (r"\barmageddon\b", 3),
    ],
    "card_draw": [
        (r"\bdraw\b.*\bcards?\b", 3),
        (r"\bdraw a card\b", 2),
        (r"\bcantrip\b", 2),
        (r"\bponder\b", 3),
        (r"\bbrainstorm\b", 3),
        (r"\bpreordain\b", 3),
        (r"\bfaithless looting\b", 2),
        (r"\bcard draw\b", 2),
        (r"\bdraw cards\b", 2),
        (r"\bwhenever.*draw\b", 1),
    ],
    "counterspell": [
        (r"\bcounter target\b", 3),
        (r"\bcounterspell\b", 3),
        (r"\bnegate\b", 3),
        (r"\bdismiss\b", 2),
        (r"\bforce of will\b", 3),
        (r"\bstifle\b", 3),
        (r"\bspell pierce\b", 2),
    ],
    "protection": [
        (r"\bprotect\b", 2),
        (r"\bindestructible\b", 2),
        (r"\bhexproof\b", 2),
        (r"\bward\b", 2),
        (r"\bshield\b", 1),
        (r"\bmake .* indestructible\b", 3),
        (r"\bgrant .* hexproof\b", 3),
    ],
    "token_maker": [
        (r"\bcreate \d+ token\b", 3),
        (r"\btoken\b.*\bcreate\b", 2),
        (r"\bhare apparent\b", 3),
        (r"\bcathars' crusade\b", 2),
        (r"\btoken maker\b", 3),
        (r"\bgo wide\b", 1),
    ],
    "lifegain": [
        (r"\bgain \d+ life\b", 2),
        (r"\blifegain\b", 2),
        (r"\blifelink\b", 1),
        (r"\bsoul sister\b", 2),
    ],
    "graveyard_hate": [
        (r"\bexile .* graveyard\b", 3),
        (r"\bgraveyard hate\b", 3),
        (r"\bgrafdigger's cage\b", 3),
        (r"\brelic of progenitus\b", 3),
        (r"\bscavenging ooze\b", 2),
    ],
    "threat": [
        (r"\bcreature\b.*\bthreat\b", 2),
        (r"\bhaste\b", 1),
        (r"\bflying\b.*\bthreat\b", 1),
        (r"\bdouble strike\b", 1),
        (r"\btrample\b", 1),
    ],
    "payoff": [
        (r"\bwhenever.*token\b", 2),
        (r"\bpayoff\b", 2),
        (r"\bengine\b", 2),
        (r"\bwin condition\b", 3),
        (r"\bcombo\b", 2),
    ],
}

# Tribe keywords extracted from type_line (e.g., "Creature — Elf Druid" → elves)
TRIBE_PATTERNS = [
    r"[Ee]lf[s]?", r"[Gg]oblin[s]?", r"[Zz]ombie[s]?", r"[Vv]ampire[s]?",
    r"[Ww]izard[s]?", r"[Ww]arrior[s]?", r"[Kk]night[s]?", r"[Dd]emon[s]?",
    r"[Dd]ragon[s]?", r"[Aa]ngel[s]?", r"[Bb]east[s]?", r"[Ii]nsect[s]?",
    r"[Hh]uman[s]?", r"[Mm]erfolk", r"[Gg]iant[s]?", r"[Ss]hapeshifter[s]?",
    r"[Cc]onstruct[s]?", r"[Aa]rtifact[s]?", r"[Ss]oldier[s]?", r"[Cc]leric[s]?",
    r"[Rr]ogue[s]?", r"[Aa]ssassin[s]?", r"[Ww]arlock[s]?",
]

# Synergy feature keywords (beyond tribes)
SYNERGY_PATTERNS = {
    "counters": r"\bcounter\b|\bproliferate\b|\+\d/+/\d+",
    "graveyard": r"\bgraveyard\b|\bfrom your graveyard\b|\bexile.*graveyard\b",
    "sacrifice": r"\bsacrifice\b|\bsac\b",
    "card_type_triggers": r"\bwhenever.*(creature|spell|artifact|enchantment|land)\b.*\b(enters|casts|dies)\b",
    "lifegain_triggers": r"\bwhenever.*gain life\b",
    "damage_triggers": r"\bwhenever.*deal.*damage\b",
    "token_triggers": r"\bwhenever.*token\b|\bcreate.*token\b",
}

# Lands that produce mana (for mana_solver integration)
MANA_PRODUCING_TYPES = {"land", "artifact"}


def norm(name):
    """Fold a card name for matching (NFKD + casefold)."""
    d = unicodedata.normalize("NFKD", name)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()


def load_pool(path=POOL):
    """Load pool.json, return dict of name -> entry."""
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data["pool"], data.get("missing", [])


def fetch_card(name):
    """Fetch a single card from Scryfall with 429 backoff. Returns dict or None."""
    url = NAMED + urllib.parse.quote(name)
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code != 429:
                raise
            if attempt == 3:
                sys.stderr.write(
                    f"Scryfall kept rate-limiting on {name!r}. "
                    "Wait a minute and re-run.\n"
                )
                raise SystemExit(1)
            wait = 5 * (attempt + 1)
            sys.stderr.write(f"  rate-limited on {name!r}, waiting {wait}s\n")
            time.sleep(wait)
    return None


def produced_mana(card):
    """Extract produced mana colors from card (lands produce their color identity)."""
    colors = set()
    type_line = (card.get("type_line") or "").lower()
    if "land" in type_line:
        ci = card.get("color_identity") or []
        colors.update(ci)
    # Check card_faces for lands too (MDFCs)
    for face in card.get("card_faces") or []:
        ft = (face.get("type_line") or "").lower()
        if "land" in ft:
            colors.update(card.get("color_identity") or [])
    return sorted(colors)


def tag_card(card):
    """Deterministically tag a card with functional roles.

    Returns set of role names. Rule-based: match Oracle text + type_line
    against ROLE_PATTERNS.
    """
    text_parts = []
    oracle_text = card.get("oracle_text") or ""
    text_parts.append(oracle_text)
    for face in card.get("card_faces") or []:
        text_parts.append(face.get("oracle_text") or "")
    text_parts.append(card.get("type_line") or "")
    full_text = " ".join(text_parts).lower()

    tags = set()
    for role, patterns in ROLE_PATTERNS.items():
        for pattern, _weight in patterns:
            if re.search(pattern, full_text):
                tags.add(role)
                break
    return tags


def extract_synergy_features(card):
    """Extract synergy features: tribes, counters, graveyard, sacrifice, etc.

    Returns dict with feature names as keys and bool/int values.
    """
    text_parts = []
    oracle_text = card.get("oracle_text") or ""
    text_parts.append(oracle_text)
    for face in card.get("card_faces") or []:
        text_parts.append(face.get("oracle_text") or "")
    full_text = " ".join(text_parts).lower()
    type_line = (card.get("type_line") or "").lower()
    # Normalize em-dash and other punctuation to spaces for tribe matching
    type_line_norm = (type_line
                      .replace(chr(0x2014), " ")  # em dash
                      .replace(chr(0x2013), " ")  # en dash
                      .replace('"', " "))
    type_line_norm = re.sub(r"\s+", " ", type_line_norm)

    features = {}

    # Tribes from type_line (simple keyword matching)
    tribes = []
    type_line_lower = type_line.lower()
    for pattern in TRIBE_PATTERNS:
        if re.search(pattern, type_line_lower):
            # Extract the tribe name from the pattern
            name = re.search(pattern, type_line_lower).group()
            # Keep the original case/form as matched
            if name not in tribes:
                tribes.append(name)
    features["tribes"] = tribes

    # Synergy keywords
    for feature, pattern in SYNERGY_PATTERNS.items():
        features[feature] = bool(re.search(pattern, full_text))

    return features


def compute_tfidf_similarity(cards):
    """Lightweight TF-IDF similarity over Oracle text for card-to-card synergy.

    Returns dict mapping card_name -> list of (other_name, similarity_score)
    for top similar cards.
    """
    # Build document-term matrix
    all_texts = []
    names = []
    for name, card in cards.items():
        text_parts = [card.get("oracle_text") or ""]
        for face in card.get("card_faces") or []:
            text_parts.append(face.get("oracle_text") or "")
        all_texts.append(" ".join(text_parts).lower())
        names.append(name)

    if not all_texts:
        return {}

    # Tokenize
    tokenized = [re.findall(r"\w+", t) for t in all_texts]

    # Document frequency
    df = Counter()
    for tokens in tokenized:
        df.update(set(tokens))

    N = len(tokenized)
    idf = {term: log(N / (freq + 1)) + 1 for term, freq in df.items()}

    # TF-IDF vectors
    vectors = []
    for tokens in tokenized:
        tf = Counter(tokens)
        vec = {term: (count / len(tokens)) * idf.get(term, 0)
               for term, count in tf.items()}
        vectors.append(vec)

    # Cosine similarity between all pairs (top N per card)
    def cosine(v1, v2):
        common = set(v1) & set(v2)
        if not common:
            return 0.0
        dot = sum(v1[t] * v2[t] for t in common)
        n1 = sum(v ** 2 for v in v1.values()) ** 0.5
        n2 = sum(v ** 2 for v in v2.values()) ** 0.5
        if n1 == 0 or n2 == 0:
            return 0.0
        return dot / (n1 * n2)

    similarities = {}
    for i, name_i in enumerate(names):
        sims = []
        for j, name_j in enumerate(names):
            if i == j:
                continue
            sim = cosine(vectors[i], vectors[j])
            if sim > 0.1:  # threshold
                sims.append((name_j, round(sim, 3)))
        sims.sort(key=lambda x: -x[1])
        similarities[name_i] = sims[:5]  # top 5

    return similarities


def enrich_pool(pool, missing=None, fetch_missing=False):
    """Enrich pool entries with full Scryfall data, tags, and synergy features.

    Args:
        pool: dict from pool.json
        missing: list of missing names (from pool.json)
        fetch_missing: if True, live-fetch missing cards from Scryfall

    Returns:
        enriched dict with same structure plus new fields per card.
    """
    enriched_pool = {}

    for name, entry in pool.items():
        enriched = dict(entry)

        # If we don't have full data, try to fetch it
        needs_fetch = (
            "oracle_text" not in enriched
            or "keywords" not in enriched
            or "card_faces" not in enriched
            or "produced_mana" not in enriched
        )
        if needs_fetch and fetch_missing:
            card = fetch_card(name)
            if card:
                enriched["oracle_text"] = card.get("oracle_text")
                enriched["keywords"] = card.get("keywords", [])
                enriched["type_line"] = card.get("type_line", "")
                enriched["color_identity"] = card.get("color_identity", [])
                enriched["produced_mana"] = produced_mana(card)
                enriched["card_faces"] = card.get("card_faces")
                enriched["legalities"] = card.get("legalities", {})
                time.sleep(DELAY)
            else:
                enriched["oracle_text"] = enriched.get("oracle_text", "")
                enriched["keywords"] = []
                enriched["produced_mana"] = produced_mana(entry)
                enriched["card_faces"] = None

        # Ensure fields exist with defaults
        enriched.setdefault("oracle_text", enriched.get("oracle_text", ""))
        enriched.setdefault("keywords", enriched.get("keywords", []))
        enriched.setdefault("type_line", enriched.get("type_line", ""))
        enriched.setdefault("produced_mana",
                          enriched.get("produced_mana") or produced_mana(entry))
        enriched.setdefault("card_faces", enriched.get("card_faces"))
        enriched.setdefault("legalities", enriched.get("legalities", {}))

        # Functional tags
        enriched["functional_roles"] = sorted(list(tag_card(enriched)))

        # Synergy features
        enriched["synergy_features"] = extract_synergy_features(enriched)

        enriched_pool[name] = enriched

    # TF-IDF similarity over all cards that have oracle text
    cards_with_text = {
        n: c for n, c in enriched_pool.items() if c.get("oracle_text")
    }
    if cards_with_text:
        similarities = compute_tfidf_similarity(cards_with_text)
        for name, sims in similarities.items():
            if name in enriched_pool:
                enriched_pool[name]["synergy_similar"] = sims

    return enriched_pool


def write_enriched(enriched_pool, missing, path=ENRICHED):
    """Write enriched pool to JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"pool": enriched_pool, "missing": missing}, fh, indent=1)
    print(f"Wrote {path} ({len(enriched_pool)} cards)")


def report(enriched_pool):
    """Print tag distribution report."""
    role_counter = Counter()
    tribe_counter = Counter()
    synergy_counter = Counter()

    for name, entry in enriched_pool.items():
        for role in entry.get("functional_roles", []):
            role_counter[role] += 1
        for tribe in entry.get("synergy_features", {}).get("tribes", []):
            tribe_counter[tribe] += 1
        for feature, val in entry.get("synergy_features", {}).items():
            if feature != "tribes" and val:
                synergy_counter[feature] += 1

    print("=== Functional Role Distribution ===")
    for role, count in role_counter.most_common():
        print(f"  {role:<20} {count}")
    print()
    print("=== Tribe Distribution ===")
    for tribe, count in tribe_counter.most_common(20):
        print(f"  {tribe:<20} {count}")
    print()
    print("=== Synergy Features ===")
    for feature, count in synergy_counter.most_common():
        print(f"  {feature:<25} {count}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", default=POOL, help="path to pool.json")
    ap.add_argument("--out", default=ENRICHED, help="output enriched pool path")
    ap.add_argument("--report", action="store_true", help="print tag distribution")
    ap.add_argument("--reuse", action="store_true",
                    help="report from existing enriched file without re-building")
    ap.add_argument("--fetch-missing", action="store_true",
                    help="live-fetch missing Scryfall fields (slow, rate-limited)")
    args = ap.parse_args()

    if args.reuse:
        if not os.path.exists(args.out):
            sys.exit(f"Enriched file not found: {args.out}")
        with open(args.out, encoding="utf-8") as fh:
            saved = json.load(fh)
        if args.report:
            report(saved["pool"])
        return

    if not os.path.exists(args.pool):
        sys.exit(f"pool.json not found at {args.pool}. Run scripts/pool.py first.")

    pool, missing = load_pool(args.pool)
    print(f"Enriching {len(pool)} cards from pool.json...")

    enriched_pool = enrich_pool(pool, missing, fetch_missing=args.fetch_missing)
    write_enriched(enriched_pool, missing, args.out)

    if args.report:
        print()
        report(enriched_pool)


if __name__ == "__main__":
    main()
