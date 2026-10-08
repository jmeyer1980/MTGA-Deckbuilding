---
name: MTGA Deckbuilding Session
description: Memory-driven MTGA deck work — build, tune, validate, or cost Ranked Standard / Ranked Brawl decks with nd-mem logging. Invoke with /mtga-deck-session.
argument-hint: What to build, tune, validate, or cost (deck name, commander/archetype, or task)
---

You are working in `C:\Users\jerio\RiderProjects\MTGA Deckbuilding`.

Inputs:
- {{input}}: The deck task — a deck file name, a commander/archetype to build around, a tune request, or a costing/legality question.

Goal:
Complete the deck task end-to-end using the neurodivergent-memory MCP tools for continuous memory capture. No GitHub issues, no PRs — this is local deck work. Decks live in `decks/` (gitignored personal data), validation is mechanical via `scripts/`, and every ownership/legality claim comes from a script run in this session, never from recall.

Workflow (execute in order):

1. Clock in + discover context:
- Call `memory_stats` to confirm the nd-mem graph is reachable.
- Run `search_memories` with `project_id="mtga-deckbuilding"` for the task (deck name, commander, archetype). Retrieve the most recent `kind:handoff` in full plus the top 2-3 related results.
- Read `README.md` session-start section if the handoff references stale tooling.

2. Refresh the two inputs (both go stale silently — always re-run, never trust files on disk):
```bash
python scripts/wildcards.py          # reads live Player.log
python scripts/pool.py --report      # rebuilds pool.json from collection.txt
```
- If `collection.txt` is stale, ask for a fresh export: Arena → Collection → export lands on the clipboard, then:
```powershell
Set-Content -Path collection.txt -NoNewline -Value (Get-Clipboard -Raw)
```
- Before substantial execution, create or update an MCP-backed plan memory on the active task thread (`project_id="mtga-deckbuilding"`). Connect new plan/task-thread nodes with `connect_memories`. Prefer `update_memory` when continuing an active slice over duplicate high-similarity logs.

3. Research and plan:
- Inspect the relevant deck file(s) in `decks/` and related memories.
- `find.py` searches the OWNED pool by effect, not name — any Scryfall query syntax works:
```bash
python scripts/find.py 'id<=W f:brawl o:"creature token"'        # owned mono-white token generators, Brawl-legal
python scripts/find.py 'id<=G f:brawl o:"add" mv<=3 -t:land'      # owned cheap green ramp
python scripts/find.py 'f:standard o:"destroy target creature"'   # owned Standard removal
python scripts/find.py 'id<=B f:brawl t:"legendary creature"' --all  # include unowned, to price in wildcards
```
- Store reasoning, plan, assumptions, and the durable principle as memories throughout. Pair substantial `practical_execution` writes with a `logical_analysis` or `creative_synthesis` memory when the rationale should outlive the task log.

4. Build / tune (the pipeline — run in order, each step is cheap, skipping one produces a list Arena rejects):
- **Pool**: `pool.py` already ran in step 2 — sums duplicate collection lines, resolves names against Scryfall, records `standard`/`brawl` legality, rarity, `mana_cost`.
- **Pick a shell**: commander or archetype first, then fill from the pool. Prefer cards already owned at the count needed; each shortfall costs a wildcard.
- **Draft** into `decks/<name>.txt` in Arena import format (`Commander` only for Brawl, `Sideboard` only for Standard, blank line between sections, `<qty> <exact card name>` per line).
- **Check**: `python scripts/deck_check.py decks/<name>.txt` — validates counts, singleton/4-of, colour identity, legality, bans, wildcard affordability, prints the curve.
- **Iterate until `legal and affordable`.** Not "legal" — affordable.
- **Hand it over** as a fenced block the user can copy straight into Arena.
- Keep storing progress notes and decisions on the same active task thread while working. Do not leave execution-only logs; each substantial implementation memory explains WHY the change exists or connects to a reasoning memory that does.

5. Self-review:
- Review the final list for curve, threat density, interaction, mana, and format rules.
- Run `deck_check.py` on the final file and quote its verdict.
- If issues found, fix before proceeding. Record validation results on the active task thread.

6. Finalize:
- Save the deck file with a versioned name (`brawl100-<commander>-v<N>.txt`, or `v<N>b` suffix for budget/owned-only variants).
- Report wildcard cost explicitly (rarity breakdown + have/after counts from `deck_check.py` output).
- Before ending, write a handoff memory (`practical_execution`, `project_id="mtga-deckbuilding"`, tag `kind:handoff`) in this format:
```
HANDOFF <date> (mtga-deckbuilding)

BUILT / CHANGED
- deck files added or edited, and why

WILDCARD STATE
- counts at session end, and what any pending build would spend

NEXT STEP
- specific enough to resume cold

CALIBRATION
- ban list / rotation as of <date>; collection export date
```
- If the work produced a reusable insight, store or update a `logical_analysis` or `creative_synthesis` memory stating the principle explicitly.
- Connect the handoff to the task thread with `connect_memories`.

Output format:
- Deck task: <what was asked>
- Plan: <numbered steps>
- Changes made: <deck files + key swaps with ownership basis>
- Validation: <deck_check.py verdict quoted + wildcard cost>
- Self-review findings: <none or list>
- Memory summary: <what was stored, why, and which durable principle or synthesis was captured>

Rules:
- Use the neurodivergent-memory MCP server continuously (decisions, progress, blockers, outcomes). Always `project_id="mtga-deckbuilding"` on writes. No exceptions.
- Core principle: verify ownership and legality mechanically, never from recall. The collection is 3,000+ cards across a decade of sets and the ban list moves every eight weeks.
- Ranked Standard + Ranked Brawl only. "Brawl" always means 100-card. `brawl*` filename → Brawl, everything else → Standard.
- Competitive (ranked) Brawl bans COMMANDERS only, nothing in the 99 — Scryfall's `brawl` field is CASUAL Brawl, `competitivebrawl` is the ranked ladder. Since 2026-10-05 `pool.py` stores both and `deck_check.py` bans against `competitivebrawl` (casual-only bans surface as a note, never an error). Verify any ban claim against Scryfall's live `competitivebrawl` value. See memory_2535.
- Give thresholds, not "it depends" — pre-committed numeric rules land well with this user (e.g. "run 24 lands at this curve", mulligan rule: 0/1/6/7 lands → mulligan, 2–5 keep).
- Record the calibration date with any ban-list or rotation claim — it expires at the next B&R announcement (~8 weeks).
- Known traps (each has cost a session — the scripts exist because of them):
  - `cmc` lies on X-spells (Meathook Massacre II reports cmc 4.0, costs 6+). Always read `mana_cost`.
  - Ban lists are invisible to observation — a banned card never appears in opponents' decks. Only a Scryfall legality pass catches bans.
  - Arena strips diacritics (`Oin the Brave` vs `Óin the Brave`). Fold with NFKD before matching.
  - Arena omits zero-valued wildcard keys — absent = 0, not unknown.
  - Duplicate collection lines (one per set block) — SUM them, don't overwrite.
  - "Any number" cards (Hare Apparent, Relentless Rats) override 4-of/singleton limits.
  - DFC/Adventure names — export writes front-face only, Scryfall returns `Front // Back`. Match on front face.
  - `api.scryfall.com` rejects WebFetch — use plain `urllib`/`curl` from a script.
- Favor connective synthesis over raw task logging: link deck memories back to reusable reasoning. Use `connect_memories` for new plan/task-thread nodes, prefer `update_memory` when continuing an existing slice.
- Include a final handoff memory at the end of the run.
- Include a final handoff memory at the end of the run.
- Do not claim completion if `deck_check.py` fails or wildcard costs are unaffordable.
- Do not treat repo-local notes, scratch docs, or TODO files as substitutes for MCP plan, progress, validation, or handoff writes.

### Session log (scripts/session_audit.py, 10-05/10-06 runs)

- 10-05 run (22 files, gap<=2.0h): RECORD 9-11-1 | rule agreement 20/20 keeps | mulligan agreement 1/1 (20:01 full 7/7 first hand, 0 lands, MULL=AGREE) | worked 18/20. 20:26 & 21:04 flagged worked=NO (T4=2).
- 10-06 run (22 files): RECORD 14-8-0 | rule agreement 20/22 keeps | mulligan agreement 0/0 (all mull games partial first hand) | worked 17/22.
  - 23:34 (brawl100-elspeth-hares-v2): hard rule disagreement — transcript 7d843bda-74ed-4fde-ab74-e250f311ea01.md (Brawl_Ladder 2026-10-06 23:34, Lost 0-1, 14 turns, Namor 9/4); keep 2x Hare Apparent · 2x Plains · Cathars' Crusade · Flawless Maneuver · Ojer Taq, Deepest Foundation; land count 2; fail-mode rule says MULL (2 stranded 4-5s Cathars' Crusade + Flawless Maneuver, no land-bridge in hand — Arcane Signet sat unused in the deck), kept, failed (worked NO). Verdict: TUNEABLE MISS, not a lucky keep (a land-bridge to the stranded pair would have flipped the rule to KEEP). Rule NOT refined — correctly flagged. Player had Plains on T1 and Hare Apparent on T3 (early plays exist); operative gate was the stranded fail-mode. Exception: 00:14 same fail-mode but WORKED (T4=4) — rule over-mulls here; exception to document, not a flaw.
  - 00:14: same fail-mode but WORKED (T4=4) — rule over-mulls here; exception to document, not a flaw.
- First-hand deduction (`seen − keep/draws/casts/plays/holding`): full-7 residuals judged; partial residuals (19:45, 23:28, 20:26) NOT judged. Elspeth's Smite-style "seen but nowhere in text" stays a documented probabilistic caveat (mtga-pbp source beyond rendered transcript).
- `--gap 0.05` → session = 2 files (00:30, 00:57), RECORD 1-1-0 — confirms gap logic.
- Temp probes (`_residual_check.py`, `_seen_probe.py`) deleted; `scripts/session_audit.py` is the only new file.

