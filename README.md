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
