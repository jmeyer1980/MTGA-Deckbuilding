#!/usr/bin/env python3
"""Build a 100-card Historic Brawl deck around Ms. Marvel, Kamala Khan.

Game plan: cast cheap spells that target YOUR OWN creatures (especially
Kamala) every turn. Each such spell draws a card and puts a +1/+1 counter on
the targeted creature via Kamala's ability. Fblthp draws on combat hits.
Protection spells double as draw triggers when they target Kamala.
"""

import json
import os
from collections import Counter

ROOT = "C:/Users/jerio/RiderProjects/MTGA Deckbuilding"
POOL = f"{ROOT}/pool.json"
DECKS_DIR = f"{ROOT}/decks"
DECK_PATH = f"{DECKS_DIR}/brawl100-ms-marvel-mono-blue.txt"

COMMANDER = "Ms. Marvel, Kamala Khan"

# Creatures -- bodies to protect/target, evasion, draw engines
CREATURES = [
    "Fblthp, Impossibly Lost",
    "Spectral Sailor",
    "Brineborn Cutthroat",
    "Cloudkin Seer",
    "Divining Duelist",
    "Facet Reader",
    "Triton Waverider",
    "Stinging Lionfish",
    "Air Elemental",
    "Bold Biochemist",
    "Chrome Host Seedshark",
    "Exclusion Mage",
    "Cryotheory Adept",
    "Elementalist Adept",
    "Bigfin Bouncer",
    "Curator of Destinies",
]

# Instants -- the engine. Heavy on "target creature you control" spells that
# draw a card (Kamala triggers: draw + +1/+1 counter). Bounce spells can target
# our own creatures to save them / re-buy ETBs.
INSTANTS = [
    # Target-creature-you-control + draw (Kamala engine)
    "Shore Up",
    "Dive Down",
    "Three Steps Ahead",
    "Thirst for Meaning",
    "Stolen Uniform",
    "Fleeting Reflection",
    "Fleeting Distraction",
    # Bounce our own creatures (Kamala trigger + reset/rebuy)
    "Unsummon",
    "Stern Dismissal",
    "Into the Roil",
    "Run Away Together",
    # Cantrip velocity
    "Consider",
    "Opt",
    "Think Twice",
    "Sleight of Hand",
    "Tune the Narrative",
    "Deduce",
    # Minimal protection / interaction
    "Spell Pierce",
    "Counterspell",
    "We Say Thee Nay!",
    "Whirlwind Denial",
    "An Offer You Can't Refuse",
    "Bounce Off",
    "Chain to Memory",
    "Spell Snare",
    "Dazzling Denial",
    "Chase Inspiration",
    "Reasonable Doubt",
]

# Sorceries -- card velocity / draw
SORCERIES = [
    "Ponder",
    "Chart a Course",
    "Divination",
    "Eyes of Gitaxias",
    "Stock Up",
    "Lunar Insight",
    "Inspiration from Beyond",
    "Seize the Secrets",
    "Flow State",
    "Shimmer of Possibility",
    "Splash Portal",
    "Procrastinate",
    "Pym Particles",
]

# Artifacts -- ramp + hand-size redundancy
ARTIFACTS = [
    "Arcane Signet",
    "Mind Stone",
    "Arc Reactor",
    "Mirror of Galadriel",
    "Soul-Guide Lantern",
]

# Lands: mostly Islands, plus utility lands I own. Reliquary Tower covers the
# no-max-hand-size redundancy.
LANDS = [
    ("Island", 33),
    ("Reliquary Tower", 1),
    ("Rogue's Passage", 1),
    ("Command Tower", 1),
    ("Cavern of Souls", 1),
]

ALL_SPELLS = CREATURES + INSTANTS + SORCERIES + ARTIFACTS

assert len(ALL_SPELLS) == 62, f"Expected 62 spells, got {len(ALL_SPELLS)}"
assert sum(q for _, q in LANDS) == 37, f"Expected 37 lands, got {sum(q for _, q in LANDS)}"


def main():
    with open(POOL, encoding="utf-8") as fh:
        pool = json.load(fh)["pool"]

    errors = []
    BASIC_LANDS = {"Island", "Plains", "Swamp", "Mountain", "Forest"}

    def check(name, want_qty):
        if name in BASIC_LANDS:
            return
        entry = pool.get(name)
        if entry is None:
            errors.append(f"NOT IN POOL: {name}")
            return
        if entry.get("qty", 0) < want_qty:
            errors.append(
                f"INSUFFICIENT QTY: {name} (need {want_qty}, own {entry.get('qty', 0)})"
            )
            return
        ci = entry.get("color_identity", [])
        if not (len(ci) == 0 or ci == ["U"]):
            errors.append(f"BAD COLOUR IDENTITY: {name} -> {ci}")
            return
        if entry.get("brawl") != "legal":
            errors.append(f"NOT BRAWL LEGAL: {name} -> {entry.get('brawl')}")
            return

    # Commander
    check(COMMANDER, 1)

    # Spells (singleton in Brawl)
    spell_counts = Counter(ALL_SPELLS)
    dupes = [n for n, c in spell_counts.items() if c > 1]
    if dupes:
        errors.append(f"DUPLICATE SPELLS (Brawl is singleton): {dupes}")
    for name in ALL_SPELLS:
        check(name, 1)

    # Lands
    for name, qty in LANDS:
        check(name, qty)

    if errors:
        print("DECK BUILD FAILED:")
        for e in errors:
            print("  -", e)
        raise SystemExit(1)

    total = 1 + len(ALL_SPELLS) + sum(q for _, q in LANDS)
    assert total == 100, f"Deck is {total} cards, expected 100"

    os.makedirs(DECKS_DIR, exist_ok=True)
    with open(DECK_PATH, "w", encoding="utf-8") as fh:
        fh.write("Commander\n")
        fh.write(f"1 {COMMANDER}\n")
        fh.write("\nDeck\n")
        for name in ALL_SPELLS:
            fh.write(f"1 {name}\n")
        for name, qty in LANDS:
            fh.write(f"{qty} {name}\n")

    print(f"Wrote {DECK_PATH} ({total} cards: 1 commander + {len(ALL_SPELLS)} spells + "
          f"{sum(q for _, q in LANDS)} lands)")
    print(f"Commander: {COMMANDER}")
    print(f"Target-own-creature instants: Shore Up, Dive Down, Three Steps Ahead, "
          f"Thirst for Meaning, Stolen Uniform, Fleeting Reflection, Fleeting Distraction")
    print(f"Owned qty verified, Brawl-legal, colour identity subset of {{U}}, singleton.")


if __name__ == "__main__":
    main()
