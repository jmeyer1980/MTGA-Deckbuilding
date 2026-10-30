#!/usr/bin/env python3
"""Score all 425 owned Standard-Brawl-eligible commanders.

Signals (per commander):
  - support depth: pool-verified legal cards with identity subset of commander
  - edhrec_rank: lower = more played as commander (log-scaled, missing = penalty)
  - game_changer flag: small bonus (marks format-warping power)
  - MV curve: bonus peaking at 2-3, decaying to 6+
  - keywords: card-advantage engines (draw, treasure, token, etc.)

Batched via /cards/collection (75/request, ~6 requests, cached to JSON).
Owned = qty>=1 only. Copy counts are NOT a ranking signal.
"""

import json
import math
import os
import time
import urllib.request

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
CACHE = f"{ROOT}/.commander_scores.json"

API = "https://api.scryfall.com/cards/collection"
UA = "jerio-mtga-deckbuilding/1.0"
BATCH = 75
DELAY = 0.12

ENGINE_WORDS = ("draw", "treasure", "token", "cascade", "discover",
                "proliferate", "blink", "reanimat", "sacrifice",
                "landfall", "prowess", "mentor")


def load_eligible():
    pool = json.load(open(POOL, encoding="utf-8"))["pool"]
    elig = {}
    for name, e in pool.items():
        if e.get("qty", 0) < 1:
            continue
        typ = e.get("type_line") or ""
        if "Legendary" not in typ or "Creature" not in typ:
            continue
        if e.get("standard") != "legal" or e.get("brawl") != "legal":
            continue
        if (e.get("competitivebrawl") or "legal") == "banned":
            continue
        elig[name] = e
    return pool, elig


def fetch_scryfall(names):
    out = {}
    names = list(names)
    for i in range(0, len(names), BATCH):
        chunk = names[i:i + BATCH]
        body = json.dumps({"identifiers": [{"name": n} for n in chunk]}).encode()
        req = urllib.request.Request(
            API, data=body,
            headers={"User-Agent": UA, "Accept": "application/json",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        for c in data.get("data", []):
            out[c["name"]] = c
        missing = [d.get("name") for d in data.get("not_found", [])]
        for m in missing:
            out[m] = None
        n = (i // BATCH) + 1
        total = math.ceil(len(names) / BATCH)
        print(f"  batch {n}/{total}: {len(data.get('data', []))} found", flush=True)
        time.sleep(DELAY)
    return out


def score(name, entry, scry, depth):
    s = scry or {}
    edh = s.get("edhrec_rank")
    if isinstance(edh, int) and edh > 0:
        # ~rank 100 -> 100pts, rank 1000 -> 67, rank 10000 -> 33, missing -> 0
        edh_pts = max(0.0, 100.0 - 33.33 * math.log10(edh))
    else:
        edh_pts = 0.0
    gc = 10.0 if s.get("game_changer") else 0.0
    cmc = entry.get("cmc") if entry.get("cmc") is not None else 99
    try:
        cmc = float(cmc)
    except (TypeError, ValueError):
        cmc = 99.0
    mv_pts = {1: 12, 2: 15, 3: 13, 4: 9, 5: 5}.get(int(cmc), 0) if cmc <= 5 else 0
    text = (s.get("oracle_text") or "").lower()
    for f in s.get("card_faces") or []:
        text += " " + (f.get("oracle_text") or "").lower()
    eng = sum(4 for w in ENGINE_WORDS if w in text)
    depth_pts = min(30.0, depth / 40.0)  # 1200 cards -> 30
    total = edh_pts + gc + mv_pts + eng + depth_pts
    return {
        "total": round(total, 1),
        "edhrec": edh, "edh_pts": round(edh_pts, 1),
        "game_changer": bool(s.get("game_changer")),
        "mv_pts": mv_pts, "engine_pts": eng,
        "depth": depth, "depth_pts": round(depth_pts, 1),
    }


def main():
    pool, elig = load_eligible()
    print(f"Eligible owned commanders: {len(elig)}")

    # support depth per commander identity
    legal_ci = {}
    for n, e in pool.items():
        if e.get("qty", 0) < 1:
            continue
        if e.get("standard") != "legal" or e.get("brawl") != "legal":
            continue
        if (e.get("competitivebrawl") or "legal") == "banned":
            continue
        legal_ci[n] = frozenset(e.get("color_identity") or [])

    depths = {}
    for n, e in elig.items():
        ci = frozenset(e.get("color_identity") or [])
        depths[n] = sum(1 for c in legal_ci.values() if c <= ci)

    # scryfall data (cached)
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
            print(f"Loaded {len(cache)} cached Scryfall records")
        except (json.JSONDecodeError, OSError):
            cache = {}
    missing = [n for n in elig if n not in cache]
    if missing:
        print(f"Fetching {len(missing)} from Scryfall...")
        fetched = fetch_scryfall(missing)
        cache.update(fetched)
        json.dump(cache, open(CACHE, "w", encoding="utf-8"))
        print(f"Cached to {CACHE}")
    else:
        print("All Scryfall data cached, no API calls needed.")

    rows = []
    for n, e in elig.items():
        sc = score(n, e, cache.get(n), depths[n])
        rows.append((n, e, sc))
    rows.sort(key=lambda r: -r[2]["total"])

    out_path = os.path.join(ROOT, "commander_scores.csv")
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write("rank,name,total,edhrec,edh_pts,mv_pts,engine_pts,depth,depth_pts,"
                "game_changer,mana_cost,cmc,colors,qty,rarity\n")
        for i, (n, e, sc) in enumerate(rows, 1):
            ci = "".join(sorted(e.get("color_identity") or [])) or "C"
            q = lambda v: f'"{v}"' if "," in str(v) else str(v)
            f.write(f"{i},{q(n)},{sc['total']},{sc['edhrec']},{sc['edh_pts']},"
                    f"{sc['mv_pts']},{sc['engine_pts']},{sc['depth']},{sc['depth_pts']},"
                    f"{sc['game_changer']},{q(e.get('mana_cost') or '')},"
                    f"{e.get('cmc')},{ci},{e.get('qty')},{e.get('rarity')}\n")
    print(f"\nWrote {out_path} ({len(rows)} rows)")

    print("\n=== Top 25 owned Standard-Brawl commanders ===")
    for i, (n, e, sc) in enumerate(rows[:25], 1):
        ci = "".join(sorted(e.get("color_identity") or [])) or "C"
        print(f"  {i:>3}  {sc['total']:>6}  edh={str(sc['edhrec']):>6}  "
              f"d={sc['depth']:>4}  {n} [{ci}] {e.get('mana_cost') or ''}")


if __name__ == "__main__":
    main()
