#!/usr/bin/env python3
"""Audit Selesnya pool for Kutzil."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "pool.json")
d = json.load(open(POOL, encoding="utf-8"))
pool = d["pool"]
print("total entries:", len(pool))
# keys present
sample = next(iter(pool.values()))
print("fields:", sorted(sample.keys()))
# counts
from collections import Counter
c = Counter()
gw_exact = []
selesnya = []  # CI subset of G,W
for name, e in pool.items():
    ci = tuple(sorted(e.get("color_identity", [])))
    c[ci] += 1
    if set(ci) <= {"G", "W"}:
        selesnya.append((name, e))
    if set(ci) == {"G", "W"}:
        gw_exact.append((name, e))
print("selesnya-identity count (C+W+G+GW):", len(selesnya))
print("GW-exact count:", len(gw_exact))
print("top identities:", c.most_common(20))
# legality breakdown for selesnya
def count(pred):
    return sum(1 for _, e in selesnya if pred(e))
print("selesnya standard==legal:", count(lambda e: e.get("standard")=="legal"))
print("selesnya competitivebrawl==legal:", count(lambda e: e.get("competitivebrawl")=="legal"))
print("selesnya brawl==legal:", count(lambda e: e.get("brawl")=="legal"))
print("has standardbrawl field?", any("standardbrawl" in e for _,e in selesnya))
# Kutzil
k = pool.get("Kutzil, Malamet Exemplar")
print("Kutzil:", k)
# GW-exact list sorted
print("\n--- GW-EXACT (57 expected) ---")
for name, e in sorted(gw_exact):
    print(f"{name} | {e.get('type_line','')[:40]} | std={e.get('standard')} cb={e.get('competitivebrawl')} b={e.get('brawl')} qty={e.get('qty')}")
# selesnya nonland standard-legal count by CI
print("\n--- SELESNYA BREAKDOWN std-legal ---")
for ci in [(), ("W",), ("G",), ("G","W")]:
    lst = [(n,e) for n,e in selesnya if tuple(sorted(e.get("color_identity",[])))==ci and e.get("standard")=="legal"]
    lands = [x for x in lst if "Land" in (x[1].get("type_line") or "")]
    non = [x for x in lst if "Land" not in (x[1].get("type_line") or "")]
    print(f"CI {ci}: total {len(lst)} (lands {len(lands)}, nonlands {len(non)})")
print("\n--- SELESNYA BREAKDOWN competitivebrawl-legal ---")
for ci in [(), ("W",), ("G",), ("G","W")]:
    lst = [(n,e) for n,e in selesnya if tuple(sorted(e.get("color_identity",[])))==ci and e.get("competitivebrawl")=="legal"]
    lands = [x for x in lst if "Land" in (x[1].get("type_line") or "")]
    non = [x for x in lst if "Land" not in (x[1].get("type_line") or "")]
    print(f"CI {ci}: total {len(lst)} (lands {len(lands)}, nonlands {len(non)})")
