"""Build the DECKS payload + rule patch for mulligan-drill.html.

Reads the live deck lists + pool.json, emits:
  mulligan-decks-v2.json      - deck entries (existing decks + current lists)
  mulligan-patch-v2.txt       - rule patch text for reference
Hares rule: fail-mode override per memory_2565.
"""
import argparse, json, os, re, subprocess

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
registry_path = os.path.join(ROOT, "mulligan-decks-v2.json")
decks = (json.load(open(registry_path, encoding="utf-8"))
         if os.path.exists(registry_path) else json.loads(txt[start:end]))
parser = argparse.ArgumentParser()
parser.add_argument("--restore-baseline", action="store_true",
                    help="restore registry entries missing from HEAD before rebuilding")
args = parser.parse_args()
if args.restore_baseline:
    baseline = json.loads(subprocess.run(
        ["git", "show", "HEAD:mulligan-decks-v2.json"], check=True,
        capture_output=True, text=True, encoding="utf-8").stdout)
    baseline_ids = {d["id"] for d in baseline}
    additions = [d for d in decks if d["id"] not in baseline_ids]
    decks = [*baseline, *additions]

pool = json.load(open(os.path.join(ROOT, "pool.json"), encoding="utf-8"))
P = pool.get("pool", pool)
cache_path = os.path.join(ROOT, ".card_cache.json")
if os.path.exists(cache_path):
    cached = json.load(open(cache_path, encoding="utf-8"))
    for name, entry in cached.items():
        P.setdefault(name, entry)

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

# Paper-only lists are enriched from local catalogs, never from Arena
# ownership. Precon cards remain usable in the trainer when absent from pool.
def add_catalog_record(record):
    name = record.get("name")
    if not name:
        return
    entry = P.setdefault(name, {})
    mappings = (
        ("type_line", ("type_line", "type")),
        ("mana_cost", ("mana_cost", "manaCost")),
        ("cmc", ("cmc", "manaValue")),
        ("color_identity", ("color_identity", "colorIdentity")),
    )
    for target, sources in mappings:
        value = next((record[source] for source in sources
                      if record.get(source) is not None), None)
        if value is not None:
            entry.setdefault(target, value)

def add_nested_catalog_records(value):
    if isinstance(value, dict):
        if value.get("name") and any(
                key in value for key in ("type", "type_line", "manaCost", "mana_cost")):
            add_catalog_record(value)
        for nested in value.values():
            add_nested_catalog_records(nested)
    elif isinstance(value, list):
        for nested in value:
            add_nested_catalog_records(nested)

for catalog_path in (
        os.path.join(ROOT, "paper", "precon-meren-plunder-the-graves.json"),
        os.path.join(ROOT, "paper", "hobbit-welcome-resolved.json"),
        os.path.join(ROOT, "paper", "precon-breya-invent-superiority.json")):
    if os.path.exists(catalog_path):
        add_nested_catalog_records(json.load(open(catalog_path, encoding="utf-8")))

PAPER_MEREN_LANDS = {
    "Cabal Coffers": {"type_line": "Land", "mana_cost": "", "cmc": 0,
                      "color_identity": ["B"]},
    "Blooming Marsh": {"type_line": "Land", "mana_cost": "", "cmc": 0,
                       "color_identity": ["B", "G"]},
    "Westvale Abbey": {"type_line": "Land", "mana_cost": "", "cmc": 0,
                       "color_identity": []},
}
for name, metadata in PAPER_MEREN_LANDS.items():
    P.setdefault(name, metadata)

PAPER_BREYA_CARDS = [
    ("Arcane Denial", "Instant", "{1}{U}", 2, ["U"]),
    ("Fact or Fiction", "Instant", "{3}{U}", 4, ["U"]),
    ("Thopter Spy Network", "Enchantment", "{2}{U}{U}", 4, ["U"]),
    ("Scrap Mastery", "Sorcery", "{3}{R}{R}", 5, ["R"]),
    ("Goblin Welder", "Creature — Goblin Artificer", "{R}", 1, ["R"]),
    ("Gilded Lotus", "Artifact", "{5}", 5, []),
    ("Swan Song", "Instant", "{U}", 1, ["U"]),
    ("Time Sieve", "Artifact", "{U}{B}", 2, ["B", "U"]),
    ("Arcum Dagsson", "Legendary Creature — Human Artificer",
     "{3}{U}", 4, ["U"]),
    ("Thopter Assembly", "Artifact Creature — Thopter", "{6}", 6, []),
    ("Master Transmuter", "Artifact Creature — Human Artificer",
     "{3}{U}", 4, ["U"]),
    ("Kuldotha Forgemaster", "Artifact Creature — Construct", "{5}", 5, []),
    ("Clock of Omens", "Artifact", "{4}", 4, []),
    ("Sword of the Meek", "Artifact — Equipment", "{2}", 2, []),
    ("Krark-Clan Ironworks", "Artifact", "{4}", 4, []),
    ("Fabricate", "Sorcery", "{2}{U}", 3, ["U"]),
    ("Nim Deathmantle", "Artifact — Equipment", "{2}", 2, []),
    ("Padeem, Consul of Innovation",
     "Legendary Creature — Vedalken Artificer", "{3}{U}", 4, ["U"]),
]
for name, type_line, mana_cost, cmc, color_identity in PAPER_BREYA_CARDS:
    add_catalog_record({
        "name": name,
        "type_line": type_line,
        "mana_cost": mana_cost,
        "cmc": cmc,
        "color_identity": color_identity,
    })

PAPER_BREYA_LANDS = {
    "Rogue's Passage": {"type_line": "Land", "mana_cost": "", "cmc": 0,
                        "color_identity": []},
}
for name, metadata in PAPER_BREYA_LANDS.items():
    P.setdefault(name, metadata)

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
    if fk: return P[fk], P[fk].get("name") or fk
    return None, None

BRIDGE = {"Ambitious Farmhand", "Knight of the White Orchid", "Loyal Warhound",
          "Arcane Signet", "The Mind Stone", "Pearl Medallion",
          "Mind Stone", "Hare Apparent", "Esper Sentinel", "Crashing Drawbridge"}
STRANDED = {"Roaming Throne", "Mondrak, Glory Dominus", "Archangel Elspeth",
            "Divine Visitation", "Cathars' Crusade", "Ojer Taq, Deepest Foundation",
            "The One Ring", "Smothering Tithe"}
# note: v21c (Jerry's running list) RUNS Divine Visitation — tag applies live now
HALF = {"Nykthos, Shrine to Nyx", "Lotus Field", "Fabled Passage"}  # tapped/slow without 2+ other lands; Fabled Passage's swap-land is tapped
COLORLESS_RISK = {"Field of Ruin", "Rogue's Passage"}

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
    cost = (entry.get("mana_cost") or "").split("//", 1)[0].strip()
    symbols = re.findall(r"\{([^}]+)\}", cost)
    if symbols:
        return sum(int(symbol) if symbol.isdigit()
                   else 0 if symbol.upper() in ("X", "Y", "Z") else 1
                   for symbol in symbols)
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
    "engine": "🐇", "utility": "🧰", "land": "🟫", "threat": "💥",
    "action": "⚡",
}
# Coarse scorer/UI roles by front-face name, curated only where useful.
ROLE = {
    # engine
    "Hare Apparent": "hare",
    "Dollmaker's Shop": "hare",
    "Optimistic Scavenger": "payoff", "Warden of the Inner Sky": "payoff",
    "Ethereal Armor": "payoff", "Elspeth, Storm Slayer": "payoff",
    "Resolute Reinforcements": "token",
    "Get Lost": "removal",
    # land-finders / rocks
    "Ambitious Farmhand": "bridge", "Knight of the White Orchid": "bridge",
    "Loyal Warhound": "bridge", "Arcane Signet": "bridge",
    "The Mind Stone": "bridge", "Pearl Medallion": "bridge",
    "Mind Stone": "bridge",
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
    "Felidar Retreat": "token", "Murdock's Crusade": "token",
    "Rabbit Response": "token", "Release the Dogs": "token",
    "Tinker's Tote": "engine", "Dollmaker's Shop": "hare",
    "Dollmaker's Shop // Porcelain Gallery": "hare",
    "On the Job": "payoff", "Split Up": "removal",
    "Banishing Light": "removal", "Elspeth's Smite": "removal",
    "Ossification": "removal", "Valorous Stance": "removal",
    "Sheltered by Ghosts": "removal", "Angel of Finality": "removal",
    "Lightning Greaves": "protect", "Swiftfoot Boots": "protect",
    # Meren paper list: roles are coarse scorer inputs, not rules.
    "Meren of Clan Nel Toth": "engine",
    "Sol Ring": "ramp", "Elvish Mystic": "ramp", "Wood Elves": "ramp",
    "Sakura-Tribe Elder": "ramp", "Golgari Signet": "ramp",
    "Thought Vessel": "ramp", "Wayfarer's Bauble": "ramp",
    "Viridian Emissary": "ramp", "Primal Growth": "ramp",
    "Golgari Charm": "removal", "Indrik Stomphowler": "removal",
    "Tribute to the Wild": "removal", "Merciless Executioner": "removal",
    "Languish": "removal", "Barter in Blood": "removal",
    "Viridian Zealot": "removal", "Shriekmaw": "removal",
    "Acidic Slime": "removal", "Sever the Bloodline": "removal",
    "Putrefy": "removal", "Phyrexian Plaguelord": "removal",
    "Victimize": "engine", "Grisly Salvage": "engine",
    "Eternal Witness": "engine", "Skullwinder": "engine",
    "Diabolic Servitude": "engine", "Scourge of Nel Toth": "engine",
    "Lotleth Troll": "engine", "Dread Summons": "engine",
    "Spider Spawning": "engine", "Satyr Wayfinder": "engine",
    "Mulch": "engine", "Bloodspore Thrinax": "payoff",
    "Mazirek, Kraul Death Priest": "payoff", "Mycoloth": "payoff",
    "Pathbreaker Ibex": "payoff", "Overwhelming Stampede": "payoff",
    "Jarad, Golgari Lich Lord": "payoff", "Bonehoard": "payoff",
    "Butcher of Malakir": "payoff", "Eater of Hope": "payoff",
    "Extractor Demon": "payoff", "Great Oak Guardian": "payoff",
    "Verdant Force": "payoff", "Cloudthresher": "payoff",
    "Terastodon": "payoff", "Vulturous Zombie": "payoff",
    "Kessig Cagebreakers": "payoff", "Eldrazi Monument": "payoff",
    "Thief of Blood": "payoff",
    "Skullclamp": "draw", "Elvish Visionary": "draw",
    "Wall of Blossoms": "draw", "Corpse Augur": "draw",
    "Phyrexian Rager": "draw", "Night's Whisper": "draw",
    "Altar's Reap": "draw",
    # Breya paper list: intentionally coarse role tags for the exploratory
    # opening-hand profile, not card-specific keep rules.
    "Breya, Etherium Shaper": "engine",
    "Sharuum the Hegemon": "engine",
    "Commander's Sphere": "ramp", "Fellwar Stone": "ramp",
    "Everflowing Chalice": "ramp", "Gilded Lotus": "ramp",
    "Etherium Sculptor": "ramp", "Chief Engineer": "ramp",
    "Blinkmoth Urn": "ramp",
    "Daretti, Scrap Savant": "engine", "Hanna, Ship's Navigator": "engine",
    "Goblin Welder": "engine", "Trash for Treasure": "engine",
    "Open the Vaults": "engine", "Scrap Mastery": "engine",
    "Beacon of Unrest": "engine", "Trading Post": "engine",
    "Myr Retriever": "engine", "Mycosynth Wellspring": "engine",
    "Ichor Wellspring": "draw", "Phyrexian Arena": "draw",
    "Fact or Fiction": "draw", "Read the Runes": "draw",
    "Baleful Strix": "draw", "Skullclamp": "draw",
    "Arcane Denial": "interaction", "Negate": "interaction",
    "Counterspell": "interaction", "Swan Song": "interaction",
    "Anguished Unmaking": "removal", "Swords to Plowshares": "removal",
    "Cyclonic Rift": "removal", "Dispeller's Capsule": "removal",
    "Goblin Cratermaker": "removal", "Nevinyrral's Disk": "removal",
    "Phyrexian Rebirth": "removal",
    "Thopter Foundry": "engine", "Sword of the Meek": "engine",
    "Time Sieve": "payoff", "Krark-Clan Ironworks": "engine",
    "Ashnod's Altar": "engine", "Thopter Assembly": "payoff",
    "Myr Battlesphere": "payoff", "Hellkite Tyrant": "payoff",
    "Jor Kadeen, the Prevailer": "payoff",
    "Cranial Plating": "payoff", "Kuldotha Forgemaster": "engine",
    "Thopter Spy Network": "engine", "Arcum Dagsson": "engine",
    "Master Transmuter": "engine", "Padeem, Consul of Innovation": "protect",
}

def kind_of(type_line, is_land):
    if is_land: return "land"
    front = (type_line or "").split("//")[0].lower()
    for k in ("creature", "artifact", "enchantment", "instant",
              "sorcery", "planeswalker", "battle"):
        if k in front: return k
    return "spell"

def build_payload(deck_id, label, deck_cards, rule, commander=None):
    new_cards = []
    lands = 0
    size = 0
    missing = []
    for qty, name in deck_cards:
        e, key = pentry(name)
        if e is None:
            missing.append(name)
            continue
        land = is_land(e, key)
        c = 0 if land else int(cmc_of(e))
        tags = []
        base = key.split(" // ")[0]
        if base in TDFC_FRONT_AS_CREATURE or key in TDFC_FRONT_AS_CREATURE:
            land = False
            c = int(cmc_of(e)) or 6
            tags.extend(("stranded", "tdfc"))
        if base in BRIDGE: tags.append("bridge")
        if base in STRANDED or key in STRANDED: tags.append("stranded")
        if base in HALF or key in HALF: tags.append("half")
        if base in COLORLESS_RISK or key in COLORLESS_RISK: tags.append("colorless")
        entry = {"n": key, "q": qty, "l": land, "c": c}
        if tags: entry["t"] = tags
        mc = e.get("mana_cost") or ""
        if (not mc) and base in ("Ojer Taq, Deepest Foundation",):
            mc = "{4}{W}{W}"
        if (not mc) and base in ("Ambitious Farmhand",):
            mc = "{1}{W}"
        if mc and not land: entry["m"] = mc
        if e.get("type_line"): entry["y"] = e["type_line"]
        if e.get("color_identity") is not None:
            entry["ci"] = e["color_identity"]
        kind = kind_of(e.get("type_line"), land)
        entry["k"] = kind
        entry["ki"] = KIND_ICON.get(kind, "🃏")
        role = ROLE.get(base) or ROLE.get(key)
        if land:
            role = "land"
        elif role is None:
            role = {"creature": "utility", "artifact": "utility",
                    "enchantment": "utility", "instant": "utility",
                    "sorcery": "utility", "planeswalker": "payoff"}.get(kind, "utility")
        entry["r"] = role
        entry["ri"] = ROLE_ICON.get(role, "🧰")
        new_cards.append(entry)
        size += qty
        if land: lands += qty

    if missing:
        raise SystemExit("missing card metadata for %s: %s" % (deck_id, ", ".join(missing)))
    print(deck_id, "size", size, "lands", lands, "ncards", len(new_cards))
    return {"id": deck_id, "label": label, "cmdr": commander,
            "size": size, "lands": lands, "cards": new_cards, "rule": rule}


new_hares = build_payload(
    "brawl100-elspeth-hares-v21c", "Elspeth Hares v21c", cards, "hares-v2",
    cmdr or "Elspeth, Storm Slayer")
if not any(d.get("id") == "brawl100-elspeth-hares-html-snapshot"
           for d in decks):
    raise SystemExit("missing canonical Elspeth HTML snapshot in trainer registry")

standard_lists = [
    ("standard60-porcelain-gallery-v1-target", "St60PG Target",
     "standard60-porcelain-gallery-v1-target.txt", "standard-pg-v1"),
    ("standard60-porcelain-gallery-v1b-owned", "St60PG Owned",
     "standard60-porcelain-gallery-v1b-owned.txt", "standard-pg-v1"),
    ("standard60-porcelain-hares-v1-target", "St60PH Target",
     "standard60-porcelain-hares-v1-target.txt", "standard-ph-v1"),
    ("standard60-porcelain-hares-v1b-owned", "St60PH Owned",
     "standard60-porcelain-hares-v1b-owned.txt", "standard-ph-v1"),
]
new_standard = []
for deck_id, label, filename, rule in standard_lists:
    path = os.path.join(ROOT, "decks", filename)
    raw = open(path, encoding="utf-8").read()
    deck_cards = []
    in_deck = False
    for line in raw.splitlines():
        line = line.strip()
        if line.lower() == "deck":
            in_deck = True
            continue
        if line.lower() == "sideboard":
            break
        if not in_deck or not line:
            continue
        match = re.match(r"^(\d+)\s+(.+)$", line)
        if match:
            deck_cards.append((int(match.group(1)), match.group(2)))
    new_standard.append(build_payload(deck_id, label, deck_cards, rule))

paper_meren_path = os.path.join(ROOT, "paper", "meren-actual-2026-10-08.txt")
paper_meren_lines = open(paper_meren_path, encoding="utf-8").read().splitlines()
paper_meren_cards = []
paper_meren_commander = None
paper_meren_section = None
for line in paper_meren_lines:
    line = line.strip()
    if line.lower() == "commander":
        paper_meren_section = "commander"
        continue
    if line.lower() == "deck":
        paper_meren_section = "deck"
        continue
    match = re.match(r"^(\d+)\s+(.+)$", line)
    if not match:
        continue
    quantity, name = int(match.group(1)), match.group(2)
    if paper_meren_section == "commander":
        if quantity != 1 or paper_meren_commander is not None:
            raise SystemExit("paper Meren source must have exactly one commander")
        paper_meren_commander = name
    elif paper_meren_section == "deck":
        paper_meren_cards.append((quantity, name))

if paper_meren_commander != "Meren of Clan Nel Toth":
    raise SystemExit("paper Meren source has an unexpected commander")
paper_meren_size = sum(quantity for quantity, _ in paper_meren_cards)
if paper_meren_size != 99:
    raise SystemExit("paper Meren library must contain 99 cards, found %d"
                     % paper_meren_size)
paper_meren = build_payload(
    "paper-meren-actual-2026-10-08", "Meren (Paper · 2026-10-08)",
    paper_meren_cards, "paper-2-5", paper_meren_commander)

paper_breya_path = os.path.join(ROOT, "paper", "breya-actual-2026-10-08.txt")
paper_breya_lines = open(paper_breya_path, encoding="utf-8").read().splitlines()
paper_breya_cards = []
paper_breya_commander = None
paper_breya_section = None
for line in paper_breya_lines:
    line = line.strip()
    if line.lower() == "commander":
        paper_breya_section = "commander"
        continue
    if line.lower() == "deck":
        paper_breya_section = "deck"
        continue
    match = re.match(r"^(\d+)\s+(.+)$", line)
    if not match:
        continue
    quantity, name = int(match.group(1)), match.group(2)
    if paper_breya_section == "commander":
        if quantity != 1 or paper_breya_commander is not None:
            raise SystemExit("paper Breya source must have exactly one commander")
        paper_breya_commander = name
    elif paper_breya_section == "deck":
        paper_breya_cards.append((quantity, name))

if paper_breya_commander != "Breya, Etherium Shaper":
    raise SystemExit("paper Breya source has an unexpected commander")
paper_breya_size = sum(quantity for quantity, _ in paper_breya_cards)
if paper_breya_size != 99:
    raise SystemExit("paper Breya library must contain 99 cards, found %d"
                     % paper_breya_size)
paper_breya = build_payload(
    "paper-breya-actual-2026-10-08",
    "Breya (Paper · 2026-10-08)",
    paper_breya_cards, "paper-2-5", paper_breya_commander)

def enrich_existing_deck(deck):
    for card in deck["cards"]:
        entry, key = pentry(card["n"])
        if entry is None:
            entry = {}
            key = card["n"]
        type_line = entry.get("type_line") or card.get("y") or ""
        base = (key or card["n"]).split(" // ")[0]
        kind = card.get("k") or kind_of(type_line, card.get("l", False))
        card.setdefault("y", type_line)
        mana_cost = entry.get("mana_cost") or ""
        if mana_cost and not card.get("l"):
            card.setdefault("m", mana_cost.split("//")[0].strip())
        if entry.get("color_identity") is not None:
            card.setdefault("ci", entry["color_identity"])
        card.setdefault("k", kind)
        card.setdefault("ki", KIND_ICON.get(kind, "🃏"))
        known_role = ROLE.get(base)
        if known_role is None:
            known_role = next((value for name, value in ROLE.items()
                               if name.casefold() == base.casefold()), None)
        fallback_role = ("land" if card.get("l") else
                         "threat" if kind in ("creature", "planeswalker") else
                         "action" if kind in ("instant", "sorcery") else "utility")
        card.setdefault("r", known_role or fallback_role)
        card.setdefault("ri", ROLE_ICON.get(card["r"], "🧰"))
    return deck

# Replace generated records in place to keep all unrelated deck order and data.
replacements = {
    d["id"]: d
    for d in [new_hares, *new_standard, paper_meren, paper_breya]
}
retired = {"brawl100-elspeth-hares", "brawl100-elspeth-hares-v21b"}
out_decks = []
for deck in decks:
    deck_id = deck["id"]
    if deck_id in retired:
        continue
    out_decks.append(enrich_existing_deck(replacements.pop(deck_id, deck)))
out_decks.extend(replacements.values())
out_decks = [enrich_existing_deck(deck) for deck in out_decks]
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
