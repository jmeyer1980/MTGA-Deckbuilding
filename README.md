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

Pool refreshes and `find.py` retry Scryfall HTTP 429 responses with bounded
backoff, then stop explicitly if the rate limit persists.

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

## Agent Integration

This project supports memory-driven issue execution using the neurodivergent-memory MCP server. The `.clinerules/workflows/mtga-deck-session.md` workflow file has been updated to support both local deck work and agent-integrated issue execution.

### Memory-Driven Issue Execution Workflow

When working with agents (e.g., `/memory-driven-issue-execution`), the following pattern is followed:

1. **Discover context**: Open the provided GitHub issues URL/scope. Start with `memory_stats` to confirm the nd-mem graph is reachable, then use `search_memories` with `project_id="mtga-deckbuilding"` to find relevant context. Read relevant memories before choosing work.

2. **Choose issue**: Pick one issue that is open, implementable, and high-value. Prioritize by highest impact first. If the highest-impact candidate appears breaking or risky, stop and ask the user for guidance before implementation. Briefly justify why this issue was selected.

3. **Research and plan**: Inspect the codebase and related files. Create a concise implementation plan. Before substantial execution, create or update an MCP-backed plan memory on the active task thread (`project_id="mtga-deckbuilding"`). Connect new plan/task-thread nodes with `connect_memories`. Prefer `update_memory` when continuing an active slice instead of creating duplicate high-similarity task logs. Store reasoning, plan, assumptions, and the durable principle behind the work as memories throughout the process.

4. **Implement**: Make the required code changes. Keep storing progress notes and decisions on the same active task thread while working. Do not leave execution-only logs; each substantial implementation memory should explain why the change exists or connect to a reasoning memory that does. Do not treat repo-local notes, scratch docs, or TODO files as substitutes for MCP plan, progress, validation, or handoff writes. Run available validation (tests/lint/build) relevant to the change.

5. **Self-review**: Review your own diff for correctness, regressions, and style consistency. If issues are found, fix them before proceeding. Record validation results on the active task thread before concluding.

6. **Finalize**: Create a draft pull request first with a concise summary, testing notes, and issue linkage. Complete self-review and any follow-up fixes. If the result is clean, commit with a clear message and transition the pull request to ready for review. Request GitHub Copilot review on the PR. Before ending, write a handoff memory that summarizes what was completed, what remains (if anything), and immediate next actions. If the work produced a reusable insight, store or update a `logical_analysis` or `creative_synthesis` memory that states the principle explicitly.

- Include a final handoff memory at the end of the run.
- Do not claim completion if tests fail or required checks are not run.
- Do not treat repo-local notes, scratch docs, or TODO files as substitutes for MCP plan, progress, validation, or handoff writes.

### Issue Workflow Details

The memory-driven issue execution workflow (as defined in GitHub Issue #9: M4.3) follows these steps:

1. **Discover context**:
   - Open the provided issues URL/scope
   - Start with `memory_stats`, then use `search_memories` or equivalent retrieval to find relevant context
   - Read relevant memories before choosing work

2. **Choose issue**:
   - Pick one issue that is open, implementable, and high-value
   - Prioritize by highest impact first
   - If the highest-impact candidate appears breaking, risky, or architecture-shifting, stop and ask the user for guidance before implementation
   - Briefly justify why this issue was selected

3. **Research and plan**:
   - Inspect the codebase and related files
   - Create a concise implementation plan
   - Before substantial execution, create or update an MCP-backed plan memory on the active task thread
   - If creating a new plan or task-thread node, connect it with `connect_memories`
   - Prefer `update_memory` when continuing an active slice instead of creating duplicate high-similarity task logs
   - Store your reasoning, plan, assumptions, and the durable principle behind the work as memories throughout the process

4. **Implement**:
   - Make the required code changes
   - Keep storing progress notes and decisions on the same active task thread while working
   - Do not leave execution-only logs; each substantial implementation memory should explain why the change exists or connect to a reasoning memory that does
   - Do not treat repo-local notes, scratch docs, or TODO files as substitutes for MCP plan, progress, validation, or handoff writes
   - If sub-agents are available and the work is bounded, delegate deliberately scoped tasks
   - Run available validation (tests/lint/build) relevant to the change

5. **Self-review**:
   - Review your own diff for correctness, regressions, and style consistency
   - If issues are found, fix them before proceeding
   - Record validation results on the active task thread before concluding

6. **Finalize**:
   - Create a draft pull request first with a concise summary, testing notes, and issue linkage
   - Complete self-review and any follow-up fixes
   - If the result is clean, commit with a clear message and transition the pull request to ready for review
   - Request GitHub Copilot review on the PR
   - Before ending, write a handoff memory that summarizes what was completed, what remains (if anything), and immediate next actions
   - If the work produced a reusable insight, store or update a `logical_analysis` or `creative_synthesis` memory that states the principle explicitly

- Selected issue: <link + short rationale>
- Plan: <numbered steps>
- Changes made: <files + key edits>
- Validation: <commands + results>
- Self-review findings: <none or list>
- Commit: <hash + message>
- PR: <link>
- Copilot review: <requested/pending/result>
- Memory summary: <what was stored, why, and which durable principle or synthesis was captured>

### Known traps (each has cost a session — the scripts exist because of them):
- `cmc` lies on X-spells (Meathook Massacre II reports cmc 4.0, costs 6+). Always read `mana_cost`.
- Ban lists are invisible to observation — a banned card never appears in opponents' decks. Only a Scryfall legality pass catches bans.
- Arena strips diacritics (`Oin the Brave` vs `Óin the Brave`). Fold with NFKD before matching.
- Arena omits zero-valued wildcard keys — absent = 0, not unknown.
- Duplicate collection lines (one per set block) — SUM them, don't overwrite.
- "Any number" cards (Hare Apparent, Relentless Rats) override 4-of/singleton limits.
- DFC/Adventure names — export writes front-face only, Scryfall returns `Front // Back`. Match on front face.
- `api.scryfall.com` rejects WebFetch — use plain `urllib`/`curl` from a script.

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