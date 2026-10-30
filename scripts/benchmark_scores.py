#!/usr/bin/env python3
"""Benchmark rows + white-bias check from commander_scores.csv."""

import csv

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
PATH = f"{ROOT}/commander_scores.csv"

rows = list(csv.DictReader(open(PATH, encoding="utf-8")))

print(f"Total ranked: {len(rows)}")

targets = {"Giada, Font of Hope", "Aurelia, the Warleader",
           "Aurelia, the Law Above", "Leonardo, Cutting Edge",
           "Danitha, Sword of Hope", "Thalia, the Survivor"}
print("\n=== Benchmarks ===")
for r in rows:
    if r["name"] in targets:
        print(f"  #{r['rank']:>3}  {r['total']:>6}  edh={r['edhrec']:>6}  "
              f"d={r['depth']:>4}  mv={r['mv_pts']:>2} eng={r['engine_pts']:>2}  "
              f"{r['name']} [{r['colors']}] {r['mana_cost']}")

print("\n=== Top 10 mono-White ===")
n = 0
for r in rows:
    if r["colors"] == "W":
        n += 1
        print(f"  #{r['rank']:>3}  {r['total']:>6}  edh={r['edhrec']:>6}  {r['name']} {r['mana_cost']}")
        if n >= 10:
            break

print("\n=== Score distribution by color count ===")
from collections import defaultdict
buckets = defaultdict(list)
for r in rows:
    buckets[len(r["colors"]) if r["colors"] != "C" else 0].append(float(r["total"]))
for k in sorted(buckets):
    vals = buckets[k]
    print(f"  {k}-color (n={len(vals):>3}): mean={sum(vals)/len(vals):.1f}  max={max(vals):.1f}")
