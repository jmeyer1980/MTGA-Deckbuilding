"""Build the new DECKS JS payload + rule patch for mulligan-drill.html.

Reads the live v21b list + pool.json, emits:
  out/mulligan-decks-v2.json   - new DECKS entries (hares rebuilt + others kept)
  out/mulligan-patch-v2.txt    - exact old/new code blocks to apply
Rule: fail-mode override per memory_2565.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = ROOT  # repo has a FILE named `out`, not a dir — write beside it


DRILL = r"C:\Users\jerio\MTGA_PlayByPlay\mulligan-drill.html"
txt = open(DRILL, encoding="utf-8").read()
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

pool = json.load(open(os.path.join(ROOT, "pool.json"), encoding="utf-8"))
P = pool.get("pool", pool)

# ---- parse live v21c (Jerry's running list, 2026-10-06) ----
raw = open(os.path.join(ROOT, "decks", "brawl100-elspeth-hares-v21c.txt"), encoding="utf-8").read()
lines = [l.strip() for l in raw.splitlines() if l.strip()]
# drop section headers
cards = []
cmdr = None
section = None
for l in lines:
    if l.lower() == "commander":
        section = "cmdr"; continue
    if l.lower() == "deck":
        section = "deck"; continue
    m = re.match(r"^(\d+)\s+(.+)$", l)
    if not m:
        continue
    qty, name = int(m.group(1)), m.group(2)
    if section == "cmdr":
        cmdr = name
    else:
        cards.append((qty, name))

def norm(n):
    import unicodedata
    d = unicodedata.normalize("NFKD", n)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()

folded = {norm(k): k for k in P}
BLANK_LANDS = {
    # collection.txt has no Plains line (basic land lines absent); pool.json
    # likewise. Basics cost nothing — hardcode rather than miss.
    "Plains": {"mana_cost": "", "cmc": 0.0, "rarity": "common",
               "type_line": "Basic Land — Plains", "color_identity": ["W"],
               "set": "basic", "qty": 999, "any_number": False,
               "standard": "legal", "brawl": "legal"},
}

# Transforming DFCs: front face is a creature, back is a land. In the opener
# they are creatures, never lands. Tag so the rule + UI treat them as spells.
TDFC_FRONT_AS_CREATURE = {
    "Ojer Taq, Deepest Foundation": "6-drop creature that converts to Temple of Civilization only after landing a hit — NOT a land in the opener",
}

def pentry(name):
    if name in P: return P[name], name
    if name in BLANK_LANDS: return BLANK_LANDS[name], name
    # DFC/Adventure: export writes front-face only ("Ambitious Farmhand"),
    # Scryfall key is full ("Ambitious Farmhand // Seasoned Cathar").
    front = name.split(" // ")[0]
    if front in P: return P[front], front
    if front in BLANK_LANDS: return BLANK_LANDS[front], front
    for key in P:
        if key.split(" // ")[0] == name or key.split(" // ")[0] == front:
            return P[key], key
    fk = folded.get(norm(name)) or folded.get(norm(front))
    if fk: return P[fk], fk
    return None, None

BRIDGE = {"Ambitious Farmhand", "Knight of the White Orchid", "Loyal Warhound",
          "Arcane Signet", "The Mind Stone", "Pearl Medallion",
          "Hare Apparent", "Esper Sentinel", "Crashing Drawbridge"}
STRANDED = {"Roaming Throne", "Mondrak, Glory Dominus", "Archangel Elspeth",
            "Divine Visitation", "Cathars' Crusade", "Ojer Taq, Deepest Foundation",
            "The One Ring", "Smothering Tithe"}
# note: v21c (Jerry's running list) RUNS Divine Visitation — tag applies live now
HALF = {"Nykthos, Shrine to Nyx", "Lotus Field", "Fabled Passage"}  # tapped/slow without 2+ other lands; Fabled Passage's swap-land is tapped
COLORLESS_RISK = {"Field of Ruin"}

def is_land(entry, name):
    t = (entry.get("type_line") or "") if entry else ""
    # TRAP (bug report 2026-10-06, screenshot): transforming DFCs like Ojer Taq
    # ("Legendary Creature — God // Land") enter as the FRONT face and can only
    # become the land later. They are NOT lands in the opener. Only MDFCs whose
    # front face is itself a land (or a true land) count as lands.
    # pool records sometimes lack type_line (e.g. Fabled Passage); fall back to
    # the types/t field so true lands are not dropped from the land count.
    if entry:
        types = entry.get("types") or entry.get("t") or []
        if "Land" in types:
            return True
    return "Land" in t

def cmc_of(entry):
    try: return float(entry.get("cmc") or 0)
    except: return 0

# ---- visual roles (QOL 2026-10-06): every card gets a face so hands read
# at a glance instead of by name. kind from type_line front face; role is
# hand-curated for v21b (bridge/stranded sets already exist for the rule).
# Icons are emoji (no assets, no font dependency).
KIND_ICON = {
    "land": "🟫", "creature": "🐇", "artifact": "⚙️", "enchantment": "✨",
    "instant": "⚡", "sorcery": "🔮", "planeswalker": "👑", "battle": "🏰",
}
ROLE_ICON = {
    "hare": "🐇", "bridge": "🌉", "draw": "📖", "removal": "🔥",
    "protect": "🛡️", "payoff": "💥", "ramp": "💧", "token": "👯",
    "utility": "🧰", "land": "🟫",
}
# role by front-face name. Keep tight: only cards in v21b + stranded set.
ROLE = {
    # engine
    "Hare Apparent": "hare",
    # land-finders / rocks
    "Ambitious Farmhand": "bridge", "Knight of the White Orchid": "bridge",
    "Loyal Warhound": "bridge", "Arcane Signet": "bridge",
    "The Mind Stone": "bridge", "Pearl Medallion": "bridge",
    "Crashing Drawbridge": "bridge",
    # draw
    "Esper Sentinel": "draw", "Mentor of the Meek": "draw",
    "Tocasia's Welcome": "draw", "Dawn of a New Age": "draw",
    "Enduring Innocence": "draw",
    # token payoffs (big bodies that end games)
    "Roaming Throne": "payoff", "Mondrak, Glory Dominus": "payoff",
    "Ojer Taq, Deepest Foundation": "payoff", "Archangel Elspeth": "payoff",
    "Cathars' Crusade": "payoff", "The One Ring": "payoff",
    "Divine Visitation": "payoff",
    "Smothering Tithe": "ramp", "Anointed Procession": "token",
    "Intangible Virtue": "token", "Oketra's Monument": "token",
    # removal
    "Lay Down Arms": "removal", "Get Lost": "removal", "Exorcise": "removal",
    "Parting Gust": "removal", "Expel the Interlopers": "removal",
    # protection
    "Teferi's Protection": "protect", "Eerie Interlude": "protect",
    "Galadriel's Dismissal": "protect", "Brave the Elements": "protect",
    "Make a Stand": "protect", "Akroma's Will": "protect",
    "Grand Abolisher": "protect", "Flawless Maneuver": "protect",
    # token makers / doublers (bodies that widen the board)
    "Caretaker's Talent": "token", "Adeline, Resplendent Cathar": "token",
    "Three Blind Mice": "token", "Hop to It": "token",
    "Toby, Beastie Befriender": "token", "Skrelv's Hive": "token",
    "The Queen of Dale": "token", "Waystone's Guidance": "token",
    "Delney, Streetwise Lookout": "payoff",
}

def kind_of(type_line, is_land):
    if is_land: return "land"
    front = (type_line or "").split("//")[0].lower()
    for k in ("creature", "artifact", "enchantment", "instant",
              "sorcery", "planeswalker", "battle"):
        if k in front: return k
    return "spell"

new_cards = []
lands = 0; size = 0
missing = []
for qty, name in cards:
    e, key = pentry(name)
    if e is None:
        missing.append(name); continue
    land = is_land(e, key)
    c = 0 if land else int(cmc_of(e))
    tags = []
    base = key.split(" // ")[0]
    if base in TDFC_FRONT_AS_CREATURE or key in TDFC_FRONT_AS_CREATURE:
        land = False  # transforming DFC: front face is a creature in opener
        c = int(cmc_of(e)) or 6
        tags.append("stranded")  # 6-drop counts toward the stranded fail-mode set
        tags.append("tdfc")
    if base in BRIDGE: tags.append("bridge")
    if base in STRANDED or key in STRANDED: tags.append("stranded")
    if base in HALF or key in HALF: tags.append("half")
    if base in COLORLESS_RISK or key in COLORLESS_RISK: tags.append("colorless")
    entry = {"n": key, "q": qty, "l": land, "c": c}
    if tags: entry["t"] = tags
    # mana_cost string: the oracle-adjacent data we DO have.
    # DFC front-face only (Ojer Taq's pool mana_cost is "" — hardcode known).
    mc = e.get("mana_cost") or ""
    if (not mc) and base in ("Ojer Taq, Deepest Foundation",):
        mc = "{4}{W}{W}"
    if (not mc) and base in ("Ambitious Farmhand",):
        mc = "{1}{W}"
    if mc and not land: entry["m"] = mc
    if e.get("type_line"): entry["y"] = e["type_line"]
    # visual face: kind + role + precomputed icons (assembler inlines CSS/JS)
    kind = kind_of(e.get("type_line"), land)
    entry["k"] = kind
    entry["ki"] = KIND_ICON.get(kind, "🃏")
    role = ROLE.get(base) or ROLE.get(key)
    if land:
        role = "land"
    elif role is None:
        # default by kind so nothing renders naked
        role = {"creature": "utility", "artifact": "utility",
                "enchantment": "utility", "instant": "utility",
                "sorcery": "utility", "planeswalker": "payoff"}.get(kind, "utility")
    entry["r"] = role
    entry["ri"] = ROLE_ICON.get(role, "🧰")
    new_cards.append(entry)
    size += qty
    if land: lands += qty

print("missing:", missing)
print("size", size, "lands", lands, "ncards", len(new_cards))

new_hares = {"id": "brawl100-elspeth-hares-v21c", "cmdr": cmdr or "Elspeth, Storm Slayer",
             "size": size, "lands": lands, "cards": new_cards,
             "rule": "hares-v2"}
# drop every prior hares revision (unversioned original + v21b) so one ships
out_decks = [d for d in decks
             if d["id"] not in ("brawl100-elspeth-hares",
                                "brawl100-elspeth-hares-v21b")]
out_decks.append(new_hares)
json.dump(out_decks, open(os.path.join(OUT, "mulligan-decks-v2.json"), "w", encoding="utf-8"), indent=1)
print("wrote mulligan-decks-v2.json")

patch = []
patch.append("OLD (single line):")
patch.append('const ruleKeep = n => n>=2 && n<=5;')
patch.append("")
patch.append("NEW:")
patch.append(open(os.path.join(HERE, "drill_rule_snippet.js"), encoding="utf-8").read() if os.path.exists(os.path.join(HERE, "drill_rule_snippet.js")) else "(snippet not yet written)")
open(os.path.join(OUT, "mulligan-patch-v2.txt"), "w", encoding="utf-8").write("\n".join(patch))
print("wrote mulligan-patch-v2.txt (placeholder until snippet lands)")
