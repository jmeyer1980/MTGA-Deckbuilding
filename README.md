# MTGA Deckbuilding

Deck construction for jerio's Arena account — **Ranked Standard** and
**Ranked Brawl** (100-card). Split out from `MTGA_PlayByPlay` so deck work and
log-parser work stop tangling.

Workflow lives in the `/mtga-deckbuilding` skill
(`~/.claude/skills/mtga-deckbuilding/SKILL.md`).
Memory scope: **`project_id: mtga-deckbuilding`**.

## Layout

```
collection.txt      Arena collection export, "<qty> <name>" per line
pool.json           generated — collection + Scryfall legality/rarity/mana_cost
.card_cache.json    generated — Scryfall lookups for cards not owned
decks/              deck lists in Arena import format
wildcard-wishlist.md  cards worth a wildcard, and what they go in
scripts/            the three tools below
```

`pool.json` and `.card_cache.json` are regenerable; delete them freely.

## Tools

```bash
python scripts/wildcards.py                  # current wildcards from Player.log
python scripts/pool.py --report              # rebuild pool.json, list bans
python scripts/deck_check.py decks/foo.txt   # validate one deck
python scripts/deck_check.py "decks/*.txt" --quiet
```

`deck_check.py` verifies counts, singleton/4-of, colour identity, format
legality, bans, wildcard affordability, and the mana curve. Format is inferred
from the filename: `brawl*` → Brawl, anything else → Standard.

## Mulligan trainer and session analysis

The canonical trainer deck registry is `mulligan-decks-v2.json`.
`scripts/drill_build_v2.py` refreshes its deck entries from the saved deck
lists and preserves the Elspeth HTML game-list snapshot as a registry entry.
`scripts/drill_assemble_v2.py` embeds the registry and shared rules in
`mulligan-drill-v2.html`. Run `scripts/drill_smoke_v2.py` and
`scripts/drill_validate_v2.py` after rebuilding, then copy the validated HTML
to `C:\Users\jerio\MTGA_PlayByPlay\mulligan-drill.html` to update the live
trainer. `scripts/session_audit.py` reads the assembled HTML, so rebuild it
before auditing new decks.

The Porcelain Gallery and Porcelain Hares Standard rules keep 2–5 land hands
only when they have a turn-1/2 board starter and at least two spells with mana
value 3 or less. Ethereal Armor counts only if the hand contains a creature
that can carry it. A five-land hand must still meet both requirements; 0/1 and
6/7 land hands are mulligans. The trainer and session audit share these
thresholds.

Paper-only lists can also be registered without being added to `pool.json` or
treated as Arena-owned/legal decks. The current Meren and Breya snapshots are
`paper/meren-actual-2026-10-08.txt` and
`paper/breya-actual-2026-10-08.txt`; each trainer entry uses the ordinary 2–5
land baseline and the same post-decision local scoring profile as every other
deck. Their scores are exploratory, not a keep rule or a power/win-rate
estimate.

### Experimental opening-hand profile

The trainer shows five local 0-100 components for every registered deck, but
only after Keep or Mulligan is chosen. The labels (velocity,
consistency, interaction, efficiency, and lethality) are inspired by
[ScryCheck's deck-level vectors](https://scrycheck.com/docs/api); its
documentation does not publish an opening-hand formula, and these scores are
not ScryCheck's scores, win probabilities, or a validated power rating. The
same generic rubric is used across deck variants and is separate from each
deck's mulligan rule:

- **Velocity:** turn-1/2/3 curve availability gated by having enough lands,
  with a bonus for a complete curve.
- **Consistency:** opener land count relative to the deck's land density, plus
  early castable options.
- **Interaction:** cheap cards tagged as removal/protection, plus cheap
  instants as a fallback response-potential proxy.
- **Efficiency:** weighted count of spells castable by turns 1, 2, and 3.
- **Lethality:** early creatures/planeswalkers and cards tagged as threats or
  payoffs/synergy.

The registry builder enriches legacy trainer decks with available pool metadata
(front-face mana cost, type, color identity, and generic role). Effects are not
inferred from Oracle text, so interaction and lethality remain coarse proxies.
Mana costs use the front face of double-faced cards; variable X/Y/Z symbols are
omitted when estimating a spell's minimum fixed cost. `session_audit.py` reports
the profile for each post-mulligan kept hand and mean component scores grouped
by deck variant. The trainer stores each profile in that deck's local ledger
and displays running per-deck means. Treat the output as an explainable
experiment, not a prediction; calibrate or revise weights only after
collecting enough results.

## Refreshing the collection

Arena → Collection → export puts the list on the clipboard:

```powershell
Set-Content -Path collection.txt -NoNewline -Value (Get-Clipboard -Raw)
```

Then re-run `python scripts/pool.py --report`.

## Snapshot — 2026-08-23

- Collection: 3,081 distinct names, 6,303 copies; 2,181 Standard-legal
- Wildcards: 20 common · 41 uncommon · 23 rare · 11 mythic
- Standard-banned cards owned: Heartfire Hero, Hopeless Nightmare,
  Monstrous Rage, Proft's Eidetic Memory, Screaming Nemesis,
  This Town Ain't Big Enough
- Brawl-banned owned: Sorcerous Spyglass

The 7 `brawl-*.txt` files (60-card) are legacy Standard Brawl — that format has
no ranked queue. The `brawl100-*.txt` files are the live ones.

## License

The code in `scripts/` is MIT licensed (see [LICENSE](LICENSE)). Collection
exports, generated caches, and deck lists are data, not code, and no license
is granted for them beyond personal use with this tool and
MTGA_Play-by-Play — see [NOTICE.md](NOTICE.md). Card data/Oracle text is
sourced via Scryfall and remains subject to
[Scryfall's Terms of Service](https://scryfall.com/docs/terms).
