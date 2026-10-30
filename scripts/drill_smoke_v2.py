r"""Smoke-test the assembled v2 drill: registry totals, required hooks, and rule syntax."""
import json, os, re
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from session_audit import (match_deck, rule_keep_standard, rule_keep_v2,
                           rule_legacy, score_opening_hand)
txt = open(os.path.join(ROOT, "mulligan-drill-v2.html"), encoding="utf-8").read()
start = txt.find("const DECKS = ") + len("const DECKS = ")
depth = 0; instr = False; esc = False; end = None
for j in range(start, len(txt)):
    ch = txt[j]
    if instr:
        if esc: esc = False
        elif ch == "\\": esc = True
        elif ch == '"': instr = False
    else:
        if ch == '"': instr = True
        elif ch == "[": depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = j + 1; break
decks = json.loads(txt[start:end])
registry = json.load(open(os.path.join(ROOT, "mulligan-decks-v2.json"),
                          encoding="utf-8"))
assert decks == registry, "assembled trainer differs from canonical registry"
print("decks:", len(decks))
assert len({d["id"] for d in decks}) == len(decks), "duplicate deck IDs"
hares = next(d for d in decks if d["id"] == "brawl100-elspeth-hares-v21c")
size = sum(c["q"] for c in hares["cards"])
lands = sum(c["q"] for c in hares["cards"] if c["l"])
print("hares size", size, "lands", lands, "rule", hares.get("rule"))
assert size == 99 and lands == 37, "totals wrong"  # 37: Ojer Taq is a TDFC creature, not a land (bug fix 2026-10-06)
expected_hares = {}
section = None
with open(os.path.join(ROOT, "decks", "brawl100-elspeth-hares-v21c.txt"),
          encoding="utf-8") as deck_file:
    for line in deck_file:
        line = line.strip()
        if line.lower() in ("commander", "deck"):
            section = line.lower()
            continue
        match = re.match(r"^(\d+)\s+(.+)$", line)
        if match and section == "deck":
            expected_hares[match.group(2).split(" // ")[0].casefold()] = int(match.group(1))
actual_hares = {c["n"].split(" // ")[0].casefold(): c["q"]
                for c in hares["cards"]}
assert actual_hares == expected_hares, "Hares trainer cards differ from v21c source"
air_temple = next(c for c in hares["cards"] if c["n"] == "Abandoned Air Temple")
assert air_temple["l"] and "half" not in air_temple.get("t", []), \
    "Abandoned Air Temple should count as a full land, not a half-land"
assert "Secluded Courtyard" not in actual_hares, \
    "retired Secluded Courtyard remains in the Hares trainer entry"
opening_17_42 = [
    "Abandoned Air Temple", "Ambitious Farmhand", "Hare Apparent",
    "Knight of the White Orchid", "Plains", "Teferi's Protection",
    "Waystone's Guidance",
]
assert rule_keep_v2(opening_17_42,
                    {c["n"].split(" // ")[0]: c for c in hares["cards"]})[0], \
    "17:42 Abandoned Air Temple opening should be KEEP under Hares v2"
print("Hares source sync and Abandoned Air Temple full-land classification ok")
snapshot = next(d for d in decks
                if d["id"] == "brawl100-elspeth-hares-html-snapshot")
snapshot_size = sum(c["q"] for c in snapshot["cards"])
snapshot_lands = sum(c["q"] for c in snapshot["cards"] if c["l"])
assert snapshot_size == 99 and snapshot_lands == 36, \
    "HTML snapshot totals wrong"
assert next(c for c in snapshot["cards"] if c["n"] == "Hare Apparent")["q"] == 26
assert next(c for c in snapshot["cards"]
            if c["n"].startswith("Dollmaker's Shop"))["c"] == 2, \
    "Room front face should be treated as a 2-drop"
assert "bridge" in next(c for c in snapshot["cards"]
                        if c["n"] == "Mind Stone")["t"]
assert "colorless" in next(c for c in snapshot["cards"]
                           if c["n"] == "Rogue's Passage")["t"]
assert all(name not in {c["n"] for c in snapshot["cards"]}
           for name in ("Anointed Procession", "Mondrak, Glory Dominus",
                        "Ojer Taq, Deepest Foundation"))
print("Elspeth HTML snapshot registry metadata ok")
emrakul = next(d for d in decks if d["id"] == "brawl100-emrakul-exigent-doom-v1b")
emrakul_size = sum(c["q"] for c in emrakul["cards"])
emrakul_lands = sum(c["q"] for c in emrakul["cards"] if c["l"])
assert emrakul["cmdr"] == "Emrakul, the Exigent Doom"
assert emrakul_size == emrakul["size"] == 99 and emrakul_lands == emrakul["lands"] == 40
assert next(c for c in emrakul["cards"] if c["n"] == "Wastes")["q"] == 28
treasure_map = next(c for c in emrakul["cards"] if c["n"].startswith("Treasure Map"))
assert not treasure_map["l"], "Treasure Map's front face is an artifact, not a land"
print("emrakul size", emrakul_size, "lands", emrakul_lands, "commander", emrakul["cmdr"])
standard_ids = [
    "standard60-porcelain-gallery-v1-target",
    "standard60-porcelain-gallery-v1b-owned",
    "standard60-porcelain-hares-v1-target",
    "standard60-porcelain-hares-v1b-owned",
]
standard = {d["id"]: d for d in decks if d["id"] in standard_ids}
assert set(standard) == set(standard_ids), "missing Standard deck variants"
source_files = {
    standard_ids[0]: "standard60-porcelain-gallery-v1-target.txt",
    standard_ids[1]: "standard60-porcelain-gallery-v1b-owned.txt",
    standard_ids[2]: "standard60-porcelain-hares-v1-target.txt",
    standard_ids[3]: "standard60-porcelain-hares-v1b-owned.txt",
}
for deck_id, d in standard.items():
    assert d["size"] == sum(c["q"] for c in d["cards"]) == 60, f"{deck_id} size"
    assert d["lands"] == sum(c["q"] for c in d["cards"] if c["l"]) == 22, f"{deck_id} lands"
    assert d["label"], f"{deck_id} missing selector label"
    assert d["rule"] == ("standard-pg-v1" if "-gallery-" in deck_id else "standard-ph-v1")
    assert all(c.get("k") and c.get("r") for c in d["cards"]), f"{deck_id} missing card face metadata"
    expected = {}
    with open(os.path.join(ROOT, "decks", source_files[deck_id]), encoding="utf-8") as deck_file:
        in_deck = False
        for line in deck_file:
            line = line.strip()
            if line.lower() == "deck":
                in_deck = True
                continue
            if line.lower() == "sideboard":
                break
            if in_deck:
                match = re.match(r"^(\d+)\s+(.+)$", line)
                if match:
                    expected[match.group(2).split(" // ")[0].casefold()] = int(match.group(1))
    actual = {c["n"].split(" // ")[0].casefold(): c["q"] for c in d["cards"]}
    assert actual == expected, f"{deck_id} cards differ from source decklist"
    print("standard ok:", d["label"], d["size"], "cards /", d["lands"], "lands")

meren = next(d for d in decks
             if d["id"] == "paper-meren-actual-2026-10-08")
assert meren["label"] == "Meren (Paper · 2026-10-08)"
assert meren["cmdr"] == "Meren of Clan Nel Toth"
assert meren["rule"] == "paper-2-5"
assert meren["size"] == sum(c["q"] for c in meren["cards"]) == 99
assert meren["lands"] == sum(c["q"] for c in meren["cards"] if c["l"]) == 37
expected_meren = {}
source_meren_counts = {}
source_commander = None
section = None
with open(os.path.join(ROOT, "paper", "meren-actual-2026-10-08.txt"),
          encoding="utf-8") as deck_file:
    for line in deck_file:
        line = line.strip()
        if line.lower() == "commander":
            section = "commander"
            continue
        if line.lower() == "deck":
            section = "deck"
            continue
        match = re.match(r"^(\d+)\s+(.+)$", line)
        if not match:
            continue
        quantity, name = int(match.group(1)), match.group(2)
        if section == "commander":
            source_commander = name
        elif section == "deck":
            expected_meren[name.casefold()] = quantity
            source_meren_counts[name] = quantity
assert source_commander == meren["cmdr"]
actual_meren = {c["n"].split(" // ")[0].casefold(): c["q"]
                for c in meren["cards"]}
assert actual_meren == expected_meren, "Meren trainer cards differ from paper source"
assert sum(expected_meren.values()) == 99
assert expected_meren["swamp"] == 14 and expected_meren["forest"] == 13
assert all(c.get("k") and c.get("r") for c in meren["cards"]), \
    "Meren missing global scoring metadata"
assert all(c.get("l") or c.get("m") for c in meren["cards"]), \
    "Meren spell missing front-face mana-cost metadata"
assert all("ci" in c for c in meren["cards"]), \
    "Meren card is missing color identity metadata"
assert all(set(c.get("ci", [])) <= {"B", "G"} for c in meren["cards"]), \
    "Meren list contains a card outside its Golgari color identity"
assert all(q == 1 or name in ("swamp", "forest")
           for name, q in expected_meren.items()), \
    "Meren singleton source has an unexpected duplicate"
matched_meren, match_score = match_deck(
    decks, meren["cmdr"], 99, set(source_meren_counts), source_meren_counts)
assert matched_meren["id"] == meren["id"] and match_score >= 190, \
    "session audit could not identify the Meren deck"
meren_byname = {c["n"].split(" // ")[0]: c for c in meren["cards"]}
x_spell_profile = score_opening_hand(
    ["Swamp", "Forest", "Dread Summons", "Eater of Hope",
     "Butcher of Malakir", "Terastodon", "Overwhelming Stampede"],
    meren_byname, meren)
assert x_spell_profile["velocity"] == 25 and x_spell_profile["efficiency"] == 18, \
    f"X spell should use its fixed mana cost: {x_spell_profile}"
print("Meren paper list ok: 100 incl. commander / 99 library / 37 lands")
print("Meren X-spell minimum-cost profile ok:", x_spell_profile)
meren_snapshot = json.load(open(
    os.path.join(ROOT, "paper", "meren-actual-state-october.json"),
    encoding="utf-8"))
assert meren_snapshot["decklist_file"] == "meren-actual-2026-10-08.txt"
assert meren_snapshot["card_counts"] == {
    "commander": 1, "library": 99, "total": 100,
    "lands": 37, "nonbasic_lands": 10, "basic_lands": 27}

breya = next(d for d in decks
             if d["id"] == "paper-breya-actual-2026-10-08")
assert breya["label"] == "Breya (Paper · 2026-10-08)"
assert breya["cmdr"] == "Breya, Etherium Shaper"
assert breya["rule"] == "paper-2-5"
assert breya["size"] == sum(c["q"] for c in breya["cards"]) == 99
assert breya["lands"] == sum(c["q"] for c in breya["cards"] if c["l"]) == 34
expected_breya = {}
source_breya_counts = {}
source_breya_commander = None
section = None
with open(os.path.join(ROOT, "paper", "breya-actual-2026-10-08.txt"),
          encoding="utf-8") as deck_file:
    for line in deck_file:
        line = line.strip()
        if line.lower() == "commander":
            section = "commander"
            continue
        if line.lower() == "deck":
            section = "deck"
            continue
        match = re.match(r"^(\d+)\s+(.+)$", line)
        if not match:
            continue
        quantity, name = int(match.group(1)), match.group(2)
        if section == "commander":
            assert source_breya_commander is None and quantity == 1
            source_breya_commander = name
        elif section == "deck":
            expected_breya[name.casefold()] = quantity
            source_breya_counts[name] = quantity
assert source_breya_commander == breya["cmdr"]
actual_breya = {c["n"].split(" // ")[0].casefold(): c["q"]
                for c in breya["cards"]}
assert actual_breya == expected_breya, \
    "Breya trainer cards differ from paper source"
assert sum(expected_breya.values()) == 99
assert all(quantity == 1 or name in
           {"mountain", "plains", "swamp", "island"}
           for name, quantity in expected_breya.items()), \
    "Breya singleton source has an unexpected duplicate"
assert all(c.get("k") and c.get("r") for c in breya["cards"]), \
    "Breya missing global scoring metadata"
assert all(c.get("l") or c.get("m") for c in breya["cards"]), \
    "Breya spell missing front-face mana-cost metadata"
assert all("ci" in c for c in breya["cards"]), \
    "Breya card is missing color identity metadata"
assert all(set(c.get("ci", [])) <= {"W", "U", "B", "R"}
           for c in breya["cards"]), \
    "Breya list contains a card outside its WUBR color identity"
matched_breya, match_score = match_deck(
    decks, breya["cmdr"], 99, set(source_breya_counts), source_breya_counts)
assert matched_breya["id"] == breya["id"] and match_score >= 190, \
    "session audit could not identify the Breya deck"
breya_land_names = {c["n"] for c in breya["cards"] if c["l"]}
assert rule_legacy(
    ["Island", "Mountain", "Sol Ring", "Swan Song", "Etherium Sculptor",
     "Baleful Strix", "Thopter Foundry"], breya_land_names)[0]
assert not rule_legacy(
    ["Island", "Sol Ring", "Swan Song", "Etherium Sculptor",
     "Baleful Strix", "Thopter Foundry", "Read the Runes"],
    breya_land_names)[0]
breya_byname = {c["n"].split(" // ")[0]: c for c in breya["cards"]}
breya_profile = score_opening_hand(
    ["Island", "Mountain", "Sol Ring", "Swan Song", "Etherium Sculptor",
     "Baleful Strix", "Thopter Foundry"], breya_byname, breya)
assert set(breya_profile) == {"velocity", "consistency", "interaction",
                              "efficiency", "lethality"}
assert all(0 <= value <= 100 for value in breya_profile.values())
breya_snapshot = json.load(open(
    os.path.join(ROOT, "paper", "breya-actual-state.json"),
    encoding="utf-8"))
assert breya_snapshot["current_user_confirmed_snapshot"]["decklist_file"] == \
    "breya-actual-2026-10-08.txt"
assert breya_snapshot["current_user_confirmed_snapshot"]["card_counts"] == {
    "commander": 1, "library": 99, "total": 100,
    "lands": 34, "short_of_commander_size": 0}
print("Breya paper list ok: 100 incl. commander / 99 library / 34 lands")
print("Breya opening-hand profile and 2–5-land baseline ok:", breya_profile)

pg = standard[standard_ids[0]]
ph = standard[standard_ids[2]]
pg_owned = standard[standard_ids[1]]
def hand_rule(deck, names):
    byname = {c["n"].split(" // ")[0]: c for c in deck["cards"]}
    return rule_keep_standard(names, byname)[0]
rule_cases = [
    (pg, ["Plains", "Plains", "Warden of the Inner Sky", "Optimistic Scavenger"], True, "PG two-land curve"),
    (ph, ["Plains", "Plains", "Hare Apparent", "Hop to It"], True, "PH Hare plus follow-up"),
    (pg, ["Plains", "Plains", "Get Lost", "Get Lost"], False, "interaction without starter"),
    (pg, ["Plains", "Plains", "Warden of the Inner Sky", "Elspeth, Storm Slayer"], False, "starter without follow-up"),
    (ph, ["Plains"] * 4 + ["Hare Apparent", "Resolute Reinforcements"], True, "four-land action hand"),
    (ph, ["Plains"] * 5 + ["Resolute Reinforcements", "Hop to It"], True, "five-land action hand"),
    (ph, ["Plains"] * 5 + ["Resolute Reinforcements", "Elspeth, Storm Slayer"], False, "five-land weak hand"),
    (pg, ["Get Lost"] * 7, False, "zero-land hand"),
    (pg, ["Plains", "Warden of the Inner Sky", "Optimistic Scavenger"], False, "one-land hand"),
    (ph, ["Plains"] * 6 + ["Hare Apparent"], False, "six-land hand"),
    (ph, ["Plains"] * 7, False, "seven-land hand"),
    (pg_owned, ["Plains", "Plains", "Optimistic Scavenger", "Ethereal Armor"], True, "live Aura with target"),
]
for deck, hand, expected, label in rule_cases:
    actual = hand_rule(deck, hand)
    assert actual == expected, f"{label}: expected {expected}, got {actual}"
    print("rule ok:", label, "KEEP" if actual else "MULL")
score_cases = [
    (pg, ["Plains", "Plains", "Warden of the Inner Sky",
          "Optimistic Scavenger", "Ethereal Armor", "Get Lost", "Hop to It"],
     "PG early curve"),
    (ph, ["Plains"] * 3 + ["Hare Apparent", "Hop to It",
                           "Caretaker's Talent", "Get Lost"],
     "PH Hare/token curve"),
]
for deck, hand, label in score_cases:
    byname = {c["n"].split(" // ")[0]: c for c in deck["cards"]}
    actual = score_opening_hand(hand, byname, deck)
    assert set(actual) == {"velocity", "consistency", "interaction",
                           "efficiency", "lethality"}, f"{label}: metrics missing"
    assert all(0 <= value <= 100 for value in actual.values()), \
        f"{label}: score out of range {actual}"
    print("score ok:", label, actual)
ph_byname = {c["n"].split(" // ")[0]: c for c in ph["cards"]}
dollmaker = next(c["n"] for c in ph["cards"]
                 if c["n"].lower().startswith("dollmaker"))
casefolded = score_opening_hand(
    ["Plains", "Plains", "Hop to It", dollmaker], ph_byname, ph)
assert casefolded["velocity"] == 25, f"DFC front-face mana cost: {casefolded}"
for deck in decks:
    expanded = [c["n"].split(" // ")[0]
                for c in deck["cards"]
                for _ in range(c.get("q", 1))]
    assert len(expanded) >= 7, f"{deck['id']} cannot deal a full hand"
    byname = {c["n"].split(" // ")[0]: c for c in deck["cards"]}
    profile = score_opening_hand(expanded[:7], byname, deck)
    assert len(profile) == 5 and all(0 <= v <= 100 for v in profile.values()), \
        f"{deck['id']} missing a global score vector: {profile}"
    assert all(c.get("k") and c.get("r") for c in deck["cards"]), \
        f"{deck['id']} missing global scoring metadata"
print("global profiles ok:", len(decks), "trainer decks")
for hook in ["ruleKeepV2", "ruleWhy", "isLandBridge", "mullDrill.v3.",
             "brawl100-elspeth-hares-v21c",
             "brawl100-elspeth-hares-html-snapshot",
             "fail-mode", "Process over outcome",
             "ruleKeepStandard", "standardStarters", "St60PG Target", "St60PH Target",
             "standard60-porcelain-gallery-v1-target",
             "turn-1/2 board starter and at least 2 spells with mana value 3 or less",
             "scoreOpeningHand", "Opening-hand profile — local heuristic",
             "scorePanel.hidden = !handScores", "not win percentages",
             "p:handScores", "profile-averages", "averages for this deck",
             "Lucky, not right",
             # visual aids (QOL 2026-10-06): faces on every card
             "class=\"legend\"", "className = \"role\"", "kindBorder",
             ".legend span", "🌉", "🐇", "c.ki", "c.ri",
             # half-land warning chrome (QOL 2026-10-05): Nykthos/Lotus Field
             # must be flagged BEFORE the call, not just in the verdict
             "--half", "card.half", "½ Land", "functional", "counts 0.5"]:
    assert hook in txt, f"missing {hook}"
    print("hook ok:", hook)
# every hares card carries kind + role + both icons (never renders naked)
for c in hares["cards"]:
    for f in ("k", "ki", "r", "ri"):
        assert c.get(f), f"{c['n']} missing {f}"
print("faces ok:", len(hares["cards"]), "cards")
score_start = txt.find("const scoreOpeningHand")
rule_start = txt.find("const ruleKeep = ", score_start)
assert score_start >= 0 and rule_start > score_start, "score function boundaries missing"
rule_why = txt.find("const ruleWhy", rule_start)
call_start = txt.find("function call(", rule_why)
score_display = txt.find("scorePanel.hidden = !handScores", call_start)
assert rule_why > rule_start and call_start > rule_why and score_display > call_start, \
    "score display must be after the user calls Keep/Mulligan"
assert txt.find("p:handScores", call_start) > score_display, \
    "the per-hand vector must be persisted only after the user call"
print("score boundaries: OK; score display stays outside the keep rule")
print("SMOKE-OK")
