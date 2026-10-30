#!/usr/bin/env python3
import json
pool = json.load(open("pool.json", encoding="utf-8"))["pool"]
cands = [
    "Guiding Hydra","Hazardroot Herbalist","Gnoll Hunter","Insidious Fungus",
    "Mutable Pupa","Pawpatch Formation","Wargling","Zack Fair","Mossborn Hydra",
    "Sumala Sentry","Wildwood Scourge","Yoshimaru, Beloved Companion",
    "Aerith Gainsborough","Drix Fatemaker","Drover Grizzly","Earth King's Lieutenant",
    "Gnarlid Colony","Knight of Wundagore","Miner's Guidewing","Sheriff of Safe Passage",
    "Beast Within","Blossoming Defense","Teferi's Protection","Swords to Plowshares",
]
for n in cands:
    e = pool.get(n)
    q = e.get("qty", 0) if e else 0
    cb = e.get("competitivebrawl") if e else "N/A"
    r = e.get("rarity") if e else "N/A"
    flag = "OWNED " if q >= 1 else "UNOWNED"
    print(f"{flag} {q}x {n:<42} {r:<8} {cb}")
