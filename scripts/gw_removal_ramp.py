#!/usr/bin/env python3
"""GW removal + ramp + protection owned (pool-verified legal)."""

import json

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"

with open(POOL, encoding="utf-8") as f:
    pool = json.load(f)["pool"]


def gw_legal(name, e):
    if e.get("qty", 0) < 1:
        return False
    if e.get("standard") != "legal" or e.get("brawl") != "legal":
        return False
    return set(e.get("color_identity") or []) <= {"G", "W"}


def show(title, pred, limit=35):
    rows = [(n, e) for n, e in pool.items() if gw_legal(n, e) and pred(n, e)]
    rows.sort(key=lambda r: (r[1].get("cmc", 9), r[0]))
    print(f"\n=== {title} ({len(rows)}) ===")
    for n, e in rows[:limit]:
        mana = e.get("mana_cost") or "?"
        print(f"  x{e.get('qty')} {mana:<12} {n} [{(e.get('type_line') or '')[:38]}]")
    return rows


def text(e):
    t = e.get("oracle_text") or ""
    for fc in e.get("card_faces") or []:
        t += " " + (fc.get("oracle_text") or "")
    return t.lower()


REMOVAL_WORDS = ("destroy target creature", "exile target",
                 "fight target", "deals damage equal")
PROT_WORDS = ("hexproof", "indestructible", "protection from",
              "can't be countered", "phase out")


def is_ramp(n, e):
    t = text(e)
    makes_mana = ("add " in t and ("{G}" in t or "{W}" in t
                                   or "add one mana" in t
                                   or "add two mana" in t))
    fetches = "search your library" in t and "land" in t
    return makes_mana or fetches


show("REMOVAL", lambda n, e: any(w in text(e) for w in REMOVAL_WORDS))
show("RAMP", is_ramp)
show("PROTECTION", lambda n, e: any(w in text(e) for w in PROT_WORDS))
