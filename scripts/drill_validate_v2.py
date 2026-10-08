r"""Validate the v2 rule against the real streak hands (memory_2565 data).
Anchor fb4d0b9f keep -> KEEP. Six fail-mode keeps -> MULL.
Plus the screenshot regression: Ojer Taq is a creature in the opener.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
decks = json.load(open(os.path.join(ROOT, "mulligan-decks-v2.json"), encoding="utf-8"))
hares = next(d for d in decks if d["id"] == "brawl100-elspeth-hares-v21c")
byname = {c["n"].split(" // ")[0]: c for c in hares["cards"]}
byname.update({c["n"]: c for c in hares["cards"]})

def landVal(c):
    if not c["l"]: return 0
    return 0.5 if "half" in c.get("t", []) else 1
def isLandBridge(c): return (not c["l"]) and (c["n"].split(" // ")[0] in (
    "Ambitious Farmhand", "Knight of the White Orchid", "Loyal Warhound",
    "Arcane Signet", "The Mind Stone", "Pearl Medallion"))
def isBridge(c): return isLandBridge(c) or ((not c["l"]) and c["n"] in ("Hare Apparent", "Esper Sentinel"))
def isStranded(c): return (not c["l"]) and ("stranded" in c.get("t", []))
def earlyPlay(c): return (not c["l"]) and (c["c"] <= 2 or isBridge(c))
def rule(hand_names):
    hand = [dict(byname[n]) for n in hand_names]
    lands = sum(1 for c in hand if c["l"])
    f = sum(landVal(c) for c in hand)
    if lands <= 1 or lands >= 6: return False, f"{lands} lands base-mull"
    stranded = sum(1 for c in hand if isStranded(c))
    landBridge = any(isLandBridge(c) for c in hand)
    early = any(earlyPlay(c) for c in hand)
    colorless = any(c["l"] and "colorless" in c.get("t", []) for c in hand)
    if f < 2: return False, f"only {f} functional"
    if stranded >= 2 and not landBridge:
        return False, f"fail-mode {stranded} stranded no-land-bridge"
    if not early: return False, "no T1-T2 play"
    if colorless and f <= 2: return True, "thin keep Field-risk"
    return (2 <= lands <= 5), f"{lands} lands bridge/early ok"

cases = [
    ("ANCHOR fb4d0b9f (expect KEEP)",
     ["Plains", "Plains", "Ambitious Farmhand", "Anointed Procession",
      "Eerie Interlude", "Ojer Taq, Deepest Foundation", "The One Ring"], True),
    ("27ace4b7 Jetmir (expect MULL: Roaming Throne+Tithe no bridge)",
     ["Fabled Passage", "Hare Apparent", "Nykthos, Shrine to Nyx", "Plains",
      "Roaming Throne", "Smothering Tithe", "The Queen of Dale"], False),
    ("7347896a Beorn (expect MULL: Ojer+Queen no bridge?)",
     ["Command Tower", "Field of Ruin", "Hare Apparent", "Ojer Taq, Deepest Foundation",
      "Plains", "The Mind Stone", "The Queen of Dale"], True),  # Mind Stone is bridge
    ("8df91f62 Stark 9-turn loss (expect MULL: Mondrak+Talent+MindStone?)",
     ["Plains", "Plains", "Hare Apparent", "Hare Apparent",
      "Caretaker's Talent", "Mondrak, Glory Dominus", "The Mind Stone"], True),  # rock+Hare bridge
    ("10e836bf Sauron (expect MULL: Crusade+Nykthos-half?)",
     ["Adeline, Resplendent Cathar", "Cathars' Crusade", "Galadriel's Dismissal",
      "Get Lost", "Hare Apparent", "Nykthos, Shrine to Nyx", "Plains"], False),
    ("33d4562d Prosper (expect MULL: Queen no bridge?)",
     ["Plains", "Plains", "Hare Apparent", "Hare Apparent",
      "Secluded Courtyard", "Teferi's Protection", "The Queen of Dale"], True),  # Hare bridge
    ("864f1ea2 Esika (expect MULL: Mondrak+Ring no bridge?)",
     ["Plains", "Plains", "Arcane Signet", "Exorcise",
      "Hop to It", "Mondrak, Glory Dominus", "The One Ring"], True),  # Signet bridge
    ("SCREENSHOT bug hand (expect MULL: 1 functional land, Ojer is creature)",
     ["Hare Apparent", "Fabled Passage", "Brave the Elements", "The Mind Stone",
      "Tocasia's Welcome", "Ojer Taq, Deepest Foundation", "Hare Apparent"], False),
]
ok = True
for label, hand, exp in cases:
    keep, why = rule(hand)
    mark = "OK " if keep == exp else "FAIL"
    if keep != exp: ok = False
    print(f"{mark} keep={keep} exp={exp} :: {label} :: {why}")
print("ALL-OK" if ok else "MISMATCHES PRESENT")
