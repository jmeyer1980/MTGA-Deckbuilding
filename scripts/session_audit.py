"""Mulligan audit for the most recent play session.

A session = a run of matches with no gap longer than --gap hours (default 2),
measured on the match timestamp in each transcript header (mtime fallback).

For every game in that session:
  - parse the opening (position, mulligan decision, kept hand, London bottoms)
  - match the transcript's deck against const DECKS in the drill HTML
    (commander + size + card-name overlap; handles the two Elspeth decks)
  - replay the kept hand through the drill's own rule: ruleKeepV2 for
    rule:"hares-v2", standard board-start rules for PG/PH, and the legacy
    2-5 lands rule otherwise
  - compute lands-by-turn-4 (3 draws on the play, 4 on the draw) = "worked"

Usage:
  py -3.12 scripts/session_audit.py
  py -3.12 scripts/session_audit.py --gap 2 --verbose
  py -3.12 scripts/session_audit.py --game-id <match-uuid>
  py -3.12 scripts/session_audit.py --dir "C:\\...\\out\\text"
"""
import argparse
import datetime
import glob
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TEXT = r"C:\Users\jerio\MTGA_PlayByPlay\out\text"
DEFAULT_DRILL = os.path.join(ROOT, "mulligan-drill-v2.html")

WORD_NUM = {"five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
WORD_NUM_LC = {k: v for k, v in WORD_NUM.items()}


# ---------------------------------------------------------------- decks ----
def parse_decks(html_path):
    txt = open(html_path, encoding="utf-8").read()
    start = txt.find("const DECKS = ") + len("const DECKS = ")
    if start < len("const DECKS = "):
        raise SystemExit("const DECKS not found in %s" % html_path)
    depth, instr, esc, end = 0, False, False, None
    for i, ch in enumerate(txt[start:], start):
        if instr:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
            continue
        if ch == '"':
            instr = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise SystemExit("unterminated DECKS array in %s" % html_path)
    return json.loads(txt[start:end])


def primary(name):
    return name.split(" // ")[0].strip()


def deck_index(deck):
    """primary-name -> card dict, set of land names."""
    byname, land_names = {}, set()
    for c in deck["cards"]:
        byname[primary(c["n"])] = c
        if c.get("l"):
            land_names.add(primary(c["n"]))
    return byname, land_names


def match_deck(decks, cmdr, n_cards, tnames, tcounts):
    """Score DECKS entries against the transcript; highest score wins."""
    best, best_score = None, -1.0
    for d in decks:
        score = 0.0
        dcmdr = d.get("cmdr")
        if cmdr and dcmdr == cmdr:
            score += 50
        elif not cmdr and not dcmdr:
            score += 10
        if d.get("size") == n_cards:
            score += 40
        dcounts = {primary(c["n"]): c["q"] for c in d["cards"]}
        if tcounts:
            overlap = sum(min(qty, dcounts.get(name, 0))
                          for name, qty in tcounts.items())
            score += 100.0 * overlap / sum(tcounts.values())
        elif tnames:
            dnames = set(dcounts)
            score += 100.0 * len(tnames & dnames) / len(tnames)
        if score > best_score:
            best, best_score = d, score
    return best, best_score


# ----------------------------------------------------------- transcripts ----
def read_lines(path):
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def header_time(lines, path):
    for l in lines[:6]:
        m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) · (Won|Lost|Drew)", l)
        if m:
            return datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M"), m.group(2)
    return datetime.datetime.fromtimestamp(os.path.getmtime(path)), "?"


def section(lines, name):
    """Lines of the '## name' section (heading excluded), stops at next '## '."""
    try:
        i = next(k for k, l in enumerate(lines) if l.startswith("## " + name))
    except StopIteration:
        return None, []
    out = []
    for l in lines[i + 1:]:
        if l.startswith("## "):
            break
        out.append(l)
    return i, out


def parse_deck_section(lines):
    """Commander, card count, all card names, and the SEEN subset
    (no '· not seen' marker = left the library at some point)."""
    _, sec = section(lines, "Your deck")
    if sec is None:
        return None, None, set(), set()
    cmdr, n_cards, names, seen, counts = None, None, set(), set(), {}
    for l in lines:
        if l.startswith("Commander: "):
            cmdr = l[len("Commander: "):].strip()
        m = re.match(r"## Your deck \((\d+) cards", l)
        if m:
            n_cards = int(m.group(1))
        m = re.match(r"^- \d+\× (.+?)(?: · not seen)?$", l)
        if m:
            name = primary(m.group(1))
            names.add(name)
            qty = re.match(r"^- (\d+)× ", l)
            counts[name] = int(qty.group(1)) if qty else 1
            if not l.endswith("· not seen"):
                seen.add(name)
    return cmdr, n_cards, names, seen, counts


def norm_card(s, seen):
    """Map log-line card text to the deck-list name. Exact first, then longest
    seen-name prefix + non-alnum delimiter ('Exorcise, targeting Tifa Lockhart')."""
    s = s.strip()
    if s in seen:
        return s
    best = None
    for cand in seen:
        if s.startswith(cand) and (len(s) == len(cand) or not s[len(cand)].isalnum()):
            if best is None or len(cand) > len(best):
                best = cand
    return best or s


def expand_qty(s):
    m = re.match(r"^(\d+)x (.+)$", s.strip())
    return m.group(2).strip() if m else s.strip()


def parse_opening(lines, opening_idx, opening):
    """-> dict(position, final_size, hand_names, bottomed, decision)."""
    on_play = any("play first" in l for l in opening)
    # Arena writes either "mulligan to 5" or "mulligan to six"
    mulls = []
    for l in opening:
        m = re.match(r"^- You mulligan to (\d+|five|six|seven|eight|nine|ten)", l, re.I)
        if m:
            tok = m.group(1).lower()
            mulls.append(int(tok) if tok.isdigit() else WORD_NUM_LC[tok])
    final_size = mulls[-1] if mulls else 7
    decision = ("mull to %d" % final_size) if mulls else "keep 7"

    # the hand list is the "- You keep ..." line carrying card data,
    # not the decision echo "- You keep seven"
    hand_line = None
    for l in opening:
        if not l.startswith("- You keep "):
            continue
        rest = l[len("- You keep "):].strip()
        if rest.lower() in WORD_NUM:
            continue
        hand_line = rest
    if hand_line is None:
        return None  # unfinished/incomplete match: no keep line to audit
    hand = []
    if hand_line:
        for p in hand_line.split("·"):
            p = p.strip()
            m = re.match(r"^(\d+)x (.+)$", p)
            if m:
                hand.extend([m.group(2).strip()] * int(m.group(1)))  # expand "2x Plains"
            elif p:
                hand.append(p)

    # London bottom(s) are logged at game start: take "is put into the library"
    # events before the first draw of the game.
    body = lines[opening_idx + 1:]
    bottomed = []
    for l in body:
        if l.startswith("- You draw "):
            break
        m = re.match(r"^- (.+) is put into the library$", l)
        if m:
            bottomed.append(m.group(1))

    # pre-bottom list (len == final + bottoms) vs already-final list
    present = [b for b in bottomed if b in hand]
    if len(hand) - len(present) == final_size:
        to_remove = list(present)
        kept = []
        for c in hand:
            if to_remove and c in to_remove:
                to_remove.remove(c)   # drop one instance per bottomed card
            else:
                kept.append(c)
        hand = kept
    elif len(hand) != final_size and bottomed:
        print("  WARNING: hand size %d != final %d (bottoms %s) — using list as-is"
              % (len(hand), final_size, bottomed))
    return {"on_play": on_play, "final_size": final_size, "decision": decision,
            "hand": hand, "bottomed": bottomed}


def t4_lands(open_lands, lines, opening_idx, on_play, land_names):
    need = 3 if on_play else 4
    draws, got = 0, 0
    for l in lines[opening_idx + 1:]:
        if l.startswith("- You draw "):
            draws += 1
            name = l[len("- You draw "):].strip()
            if primary(name) in land_names:
                got += 1
            if draws >= need:
                break
    return open_lands + got


# ----------------------------------------------------------------- rule ----
def rule_keep_v2(hand, byname):
    """Port of drill's ruleKeepV2 (mulligan-drill-v2.html)."""
    cards = [byname.get(primary(n), {"n": n, "l": False, "c": 99, "t": []}) for n in hand]
    def land_val(c):
        if not c.get("l"):
            return 0
        return 0.5 if "half" in (c.get("t") or []) else 1
    def is_land_bridge(c):
        return (not c.get("l")) and primary(c["n"]) in (
            "Ambitious Farmhand", "Knight of the White Orchid", "Loyal Warhound",
            "Arcane Signet", "The Mind Stone", "Mind Stone", "Pearl Medallion")
    def is_bridge(c):
        return is_land_bridge(c) or (
            (not c.get("l")) and primary(c["n"]) in ("Hare Apparent", "Esper Sentinel"))
    def is_stranded(c):
        return (not c.get("l")) and "stranded" in (c.get("t") or [])
    def early_play(c):
        return (not c.get("l")) and (c.get("c", 99) <= 2 or is_bridge(c))

    lands = sum(1 for c in cards if c.get("l"))
    f = sum(land_val(c) for c in cards)
    if lands <= 1 or lands >= 6:
        return False, "%d lands — base rule mulls 0/1/6/7" % lands
    stranded = sum(1 for c in cards if is_stranded(c))
    land_bridge = any(is_land_bridge(c) for c in cards)
    early = any(early_play(c) for c in cards)
    colorless_risk = any(c.get("l") and "colorless" in (c.get("t") or []) for c in cards)
    if f < 2:
        return False, "only %s functional lands (Nykthos/Lotus Field count half)" % f
    if stranded >= 2 and not land_bridge:
        return False, "fail-mode: %d stranded 4-5s with no land-finder/rock" % stranded
    if not early:
        return False, "no play before turn 3"
    if colorless_risk and f <= 2:
        return True, "keep, thin: colorless land toward WW-by-5"
    return (2 <= lands <= 5), "%d lands with bridge/early action" % lands


def rule_legacy(hand, land_names):
    lands = sum(1 for n in hand if primary(n) in land_names)
    return (2 <= lands <= 5), "%d lands — base 2-5 rule" % lands


def rule_keep_standard(hand, byname):
    """Port of drill's PG/PH keep rule: starter plus two early actions."""
    cards = [byname.get(primary(n), {"n": n, "l": False, "c": 99}) for n in hand]
    lands = sum(1 for c in cards if c.get("l"))
    if lands <= 1 or lands >= 6:
        return False, "%d lands — mulligan 0/1/6/7" % lands
    starters = {"Optimistic Scavenger", "Warden of the Inner Sky",
                "Resolute Reinforcements", "Hare Apparent"}
    has_starter = any(not c.get("l") and primary(c["n"]) in starters for c in cards)
    has_armor_target = any(
        not c.get("l") and primary(c["n"]) in starters for c in cards)
    actions = sum(
        1 for c in cards
        if not c.get("l") and c.get("c", 99) <= 3
        and (primary(c["n"]) != "Ethereal Armor" or has_armor_target))
    if not has_starter:
        return False, "no turn-1/2 board starter (Scavenger, Warden, Reinforcements, or Hare)"
    if actions < 2:
        return False, "board starter but fewer than 2 spells with mana value 3 or less"
    if lands == 5:
        return True, "5 lands kept only with a board starter and 2 spells with mana value 3 or less"
    return True, "%d lands with a board starter and 2 spells with mana value 3 or less" % lands


def score_opening_hand(hand, byname, deck):
    """Global local opening-hand rubric; component scores are not probabilities."""
    normalized = {primary(name).casefold(): card for name, card in byname.items()}
    cards = [normalized.get(primary(n).casefold(),
                            {"n": n, "l": False, "m": "", "c": 0,
                             "k": "", "r": ""})
             for n in hand]
    playable = [c for c in cards if not c.get("l")]

    def mana_value(card):
        cost = (card.get("m") or "").split("//")[0]
        if not cost:
            return card.get("c", 0)
        total = 0
        for symbol in re.findall(r"\{([^}]+)\}", cost):
            numeric = re.findall(r"\d+", symbol)
            if numeric:
                total += max(map(int, numeric))
            elif symbol.upper() not in ("X", "Y", "Z"):
                total += 1
        return total

    t1 = sum(1 for c in playable if mana_value(c) <= 1)
    t2 = sum(1 for c in playable if mana_value(c) == 2)
    t3 = sum(1 for c in playable if mana_value(c) == 3)
    lands = sum(1 for c in cards if c.get("l"))
    has_t1, has_t2, has_t3 = lands >= 1 and t1 > 0, lands >= 2 and t2 > 0, lands >= 3 and t3 > 0
    expected_lands = 7 * (deck.get("lands") or 0) / (deck.get("size") or 60)
    land_fit = max(0, 100 - abs(lands - expected_lands) * 28)
    kind = lambda c: c.get("k") or ""
    role = lambda c: (c.get("r") or "").lower()
    interaction_cards = sum(
        1 for c in playable
        if role(c) in ("removal", "protect", "interaction")
        or (kind(c) == "instant" and mana_value(c) <= 3))
    threat_cards = sum(
        1 for c in playable
        if role(c) in ("threat", "payoff", "hare")
        or (kind(c) in ("creature", "planeswalker") and mana_value(c) <= 4))
    synergy_cards = sum(
        1 for c in playable
        if role(c) in ("payoff", "hare", "token", "engine"))
    fast_threats = sum(
        1 for c in playable
        if ((kind(c) in ("creature", "planeswalker")
             or role(c) in ("threat", "payoff", "hare"))
            and mana_value(c) <= 3))

    return {
        "velocity": ((35 if has_t1 else 0) + (25 if has_t2 else 0)
                     + (15 if has_t3 else 0)
                     + (25 if has_t1 and has_t2 and has_t3 else 0)),
        "consistency": min(100, int(land_fit * 0.75
                                    + min(100, (t1 + t2 + t3) * 25) * 0.25 + 0.5)),
        "interaction": min(100, interaction_cards * 35),
        "efficiency": min(100, t1 * 28 + t2 * 18 + t3 * 8),
        "lethality": min(100, fast_threats * 20 + synergy_cards * 12
                         + max(0, threat_cards - fast_threats) * 8),
    }


def rule_for_deck(deck, hand, byname, land_names):
    if deck.get("rule") == "hares-v2":
        return rule_keep_v2(hand, byname)
    if deck.get("rule") in ("standard-pg-v1", "standard-ph-v1"):
        return rule_keep_standard(hand, byname)
    return rule_legacy(hand, land_names)


def deduce_first_hand(lines, opening_idx, seen, kept_hand, decision):
    """Cards marked SEEN but absent from every post-opening event = the
    rejected first hand (mulligan games) or unexplained residue (keep games).

    Returns (cards, kind) where kind is 'first-hand', 'residue', or 'none'.
    """
    accounted = set(kept_hand)
    for l in lines[opening_idx + 1:]:
        for tag in ("- You draw ", "- You cast ", "- You play "):
            if l.startswith(tag):
                accounted.add(norm_card(l[len(tag):], seen))
        if l.startswith("- You end holding "):
            for p in l[len("- You end holding "):].split("·"):
                accounted.add(norm_card(expand_qty(p), seen))
    residual = sorted(seen - accounted)
    if not decision.startswith("mull"):
        return residual, ("residue" if residual else "none")
    return residual, "first-hand"


# ----------------------------------------------------------------- main ----
def find_session(text_dir, gap_hours):
    """Newest transcript + all ancestors forming a run with gaps <= gap_hours."""
    files = glob.glob(os.path.join(text_dir, "*.md"))
    if not files:
        raise SystemExit("no transcripts in %s" % text_dir)
    dated = []
    for f in files:
        lines = read_lines(f)
        ts, res = header_time(lines, f)
        dated.append((ts, f, res, lines))
    dated.sort(key=lambda x: x[0])
    session = [dated[-1]]
    i = len(dated) - 2
    while i >= 0:
        if (session[0][0] - dated[i][0]).total_seconds() / 3600.0 > gap_hours:
            break
        session.insert(0, dated[i])
        i -= 1
    return session


def find_game(text_dir, game_id):
    """Return only the transcript whose filename stem exactly matches game_id."""
    files = glob.glob(os.path.join(text_dir, "*.md"))
    matches = [f for f in files
               if os.path.splitext(os.path.basename(f))[0].casefold()
               == game_id.casefold()]
    if not matches:
        raise SystemExit("no transcript for game ID %s in %s" % (game_id, text_dir))
    if len(matches) > 1:
        raise SystemExit("multiple transcripts for game ID %s in %s" % (game_id, text_dir))
    path = matches[0]
    lines = read_lines(path)
    ts, res = header_time(lines, path)
    return [(ts, path, res, lines)]


def main():
    ap = argparse.ArgumentParser(description="Audit mulligan decisions for a session or one game.")
    ap.add_argument("--dir", default=DEFAULT_TEXT, help="transcript dir (default: %(default)s)")
    ap.add_argument("--drill", default=DEFAULT_DRILL, help="drill html (default: %(default)s)")
    ap.add_argument("--gap", type=float, default=2.0, help="max hours between matches in a session")
    ap.add_argument("--verbose", action="store_true", help="print every kept hand")
    ap.add_argument("--game-id", help="audit only the transcript named <game-id>.md")
    args = ap.parse_args()

    decks = parse_decks(args.drill)
    session = (find_game(args.dir, args.game_id) if args.game_id
               else find_session(args.dir, args.gap))

    span = "%s -> %s" % (session[0][0].strftime("%m-%d %H:%M"),
                         session[-1][0].strftime("%m-%d %H:%M"))
    if args.game_id:
        print("GAME ID %s  (%s, %s)" %
              (os.path.splitext(os.path.basename(session[0][1]))[0], span, session[0][2]))
        missing_note = next((line[2:] for line in session[0][3]
                             if line.startswith("> Part of this match is missing")), None)
        if missing_note:
            print("TRANSCRIPT CAVEAT: %s" % missing_note)
        print("WORKED = turn-four land threshold (3 lands on play / 4 on draw), not the keep-rule verdict.")
    else:
        print("SESSION %s  (%d files, gap <= %.1fh)" % (span, len(session), args.gap))
    print()

    hdr = "%-6s %-5s %-6s %-16s %-6s %-6s %-5s %-8s %-24s %s"
    print(hdr % ("TIME", "RES", "POS", "DECISION", "LANDS", "T4LAND", "RULE",
                 "AGREE?", "PROFILE", "WORKED"))
    n_agree = n_decided = n_worked = n_playable = 0
    n_mull = n_mull_agree = 0
    profile_groups = {}
    wl = {"Won": 0, "Lost": 0, "Drew": 0}
    problems = []

    for ts, path, res, lines in session:
        tm = ts.strftime("%H:%M")
        oi, opening = section(lines, "Opening")
        wl[res] = wl.get(res, 0) + 1
        if oi is None or not opening:
            print(hdr % (tm, res, "-", "(no opening)", "-", "-", "-", "-", "-", "-"))
            continue
        n_playable += 1
        cmdr, n_cards, tnames, seen, tcounts = parse_deck_section(lines)
        deck, score = match_deck(decks, cmdr, n_cards, tnames, tcounts)
        byname, land_names = deck_index(deck)

        op = parse_opening(lines, oi, opening)
        if op is None:
            print(hdr % (tm, res, "-", "(no keep line)", "-", "-", "-", "-", "-", "-"))
            continue
        hand = op["hand"]
        open_lands = sum(1 for n in hand if primary(n) in land_names)
        t4 = t4_lands(open_lands, lines, oi, op["on_play"], land_names)
        worked = 3 <= t4 <= 5

        keep, why = rule_for_deck(deck, hand, byname, land_names)
        profile = score_opening_hand(hand, byname, deck)
        profile_text = " ".join("%s%d" % (key[0].upper(), value)
                                for key, value in profile.items())
        group = deck.get("label") or deck["id"]
        group_totals = profile_groups.setdefault(
            group, {key: 0 for key in profile})
        group_totals["n"] = group_totals.get("n", 0) + 1
        for key, value in profile.items():
            group_totals[key] += value

        n_decided += 1
        n_agree += keep           # his final action is always a keep; rule must say keep
        n_worked += worked
        agree = "yes" if keep else "**NO**"
        if not keep:
            problems.append((tm, "rule says MULL but hand was kept: " + why))
        if not worked:
            problems.append((tm, "hand did not work (T4 lands=%d)" % t4))

        print(hdr % (tm, res, "play" if op["on_play"] else "draw", op["decision"],
                     open_lands, t4, "KEEP" if keep else "MULL", agree,
                     profile_text,
                     "yes" if worked else "NO"))

        # deduction: seen cards never accounted for by hand/draw/cast/play/holding
        residual, kind = deduce_first_hand(lines, oi, seen, hand, op["decision"])
        if kind == "first-hand":
            fh_lands = sum(1 for n in residual if primary(n) in land_names)
            if len(residual) == 7:
                # full rejected hand: judge the mulligan decision itself
                fh_keep, fh_why = rule_for_deck(deck, residual, byname, land_names)
                verdict = "rule %s" % ("KEEP" if fh_keep else "MULL")
                ok = not fh_keep          # he mulliganed; rule must agree
                n_mull += 1
                n_mull_agree += ok
                if not ok:
                    problems.append((tm, "mulligan DISAGREED: rejected hand was a keeper (%s)" % fh_why))
                print("       first hand (deduced, full 7): %d lands — %s  [%s]"
                      % (fh_lands, verdict, "AGREE" if ok else "**DISAGREE**"))
                print("         %s" % " | ".join(residual))
            elif residual:
                print("       first hand (deduced, partial %d/7, %d lands): %s"
                      % (len(residual), fh_lands, " | ".join(residual)))
        elif kind == "residue":
            print("       NOTE: %d seen-but-unaccounted card(s) despite keep: %s"
                  % (len(residual), " | ".join(residual)))

        if args.verbose or args.game_id:
            print("       deck=%s (score %.0f, rule=%s)" % (deck["id"], score, deck.get("rule") or "legacy"))
            print("       why: %s" % why)
            print("       hand: %s" % " | ".join(hand))
            if op["bottomed"]:
                print("       bottomed: %s" % ", ".join(op["bottomed"]))
            # seen but never cast/played (excludes lands still in hand at end is impossible:
            # end-holding is accounted, so this = seen - casts - plays - holding)
            casts = {norm_card(l[len("- You cast "):], seen) for l in lines if l.startswith("- You cast ")}
            casts |= {norm_card(l[len("- You play "):], seen) for l in lines if l.startswith("- You play ")}
            np = sorted(seen - casts)
            print("       seen but never played: %s" % (" | ".join(np) if np else "(none)"))
        elif score < 90 and deck.get("cmdr") != cmdr:
            print("       WARNING: weak deck match %s (score %.0f) for cmdr=%s" % (deck["id"], score, cmdr))

    print()
    print("RECORD %d-%d-%d  |  rule agreement %d/%d keeps  |  mulligan agreement %d/%d  |  worked %d/%d"
          % (wl["Won"], wl["Lost"], wl["Drew"], n_agree, n_decided,
             n_mull_agree, n_mull, n_worked, n_decided))
    if profile_groups:
        print("Post-mulligan kept-hand profile means by deck (0-100 heuristic, not win probability):")
        for group, totals in profile_groups.items():
            print("  %s (n=%d): %s"
                  % (group, totals["n"], "  ".join(
                      "%s=%d" % (key, round(totals[key] / totals["n"]))
                      for key in ("velocity", "consistency", "interaction",
                                  "efficiency", "lethality"))))
    if problems:
        print("FLAGS:")
        for tm, msg in problems:
            print("  %s  %s" % (tm, msg))


if __name__ == "__main__":
    main()
