r"""Assemble the full patched mulligan-drill.html (v2) in-repo for review.

Reads C:\Users\jerio\MTGA_PlayByPlay\mulligan-drill.html, applies:
  1. new DECKS payload (mulligan-decks-v2.json)
  2. rule snippet (scripts/drill_rule_snippet.js)
  3. call()/deal()/render() upgrades (reason pills, mana_cost display, v3 ledger key)
Writes mulligan-drill-v2.html at repo root for review + copy-over.
Does NOT touch the PlayByPlay file.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DRILL = r"C:\Users\jerio\MTGA_PlayByPlay\mulligan-drill.html"
txt = open(DRILL, encoding="utf-8").read()

new_decks = json.load(open(os.path.join(ROOT, "mulligan-decks-v2.json"), encoding="utf-8"))
snippet = open(os.path.join(HERE, "drill_rule_snippet.js"), encoding="utf-8").read()

def add_hand_score_ui(text):
    """Add the post-decision-only score panel to either trainer source."""
    text = text.replace("standardHandScore", "scoreOpeningHand")
    text = text.replace(
        "Category names are inspired by ScryCheck; these PG/PH hand scores use a separate, uncalibrated local rubric.",
        "Category names are inspired by ScryCheck's deck-level vectors; these scores are local heuristics for every trainer deck.")
    if 'id="handscore"' not in text:
        css_anchor = "  .draws{display:flex;flex-wrap:wrap;gap:6px}"
        assert css_anchor in text, "draw styles not found"
        text = text.replace(css_anchor, """  .hand-score{border:1px solid var(--line);border-radius:8px;padding:12px;margin:14px 0;background:var(--surface-2)}
  .score-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin-top:10px}
  .score-item{display:grid;grid-template-columns:1fr auto;gap:5px 8px;font-family:var(--mono);font-size:11px;text-transform:capitalize}
  .score-item progress{grid-column:1 / -1;width:100%;height:8px;accent-color:var(--accent)}
""" + css_anchor, 1)
        html_anchor = '          <div class="verdict" id="verdict"></div>'
        assert html_anchor in text, "verdict panel not found"
        text = text.replace(html_anchor, html_anchor + """
          <section class="hand-score" id="handscore" hidden aria-label="Exploratory opening-hand profile">
            <strong>Opening-hand profile — local heuristic</strong>
            <p class="note">0–100 component scores, not win percentages or a keep rule. Category names are inspired by ScryCheck's deck-level vectors; these scores are local heuristics for every trainer deck.</p>
            <div class="score-grid" id="score-items"></div>
          </section>""", 1)
        js_anchor = "  const rk = why.keep;"
        assert js_anchor in text, "call rule result not found"
        score_js = """      const handScores = scoreOpeningHand(hand, deck);
  const scorePanel = $("#handscore");
  scorePanel.hidden = !handScores;
  const scoreItems = $("#score-items"); scoreItems.innerHTML = "";
  if (handScores) Object.entries(handScores).forEach(([metric, value]) => {
    const item = document.createElement("div"); item.className = "score-item";
    const label = document.createElement("span"); label.textContent = metric;
    const score = document.createElement("b"); score.textContent = value + "/100";
    const meter = document.createElement("progress"); meter.max = 100; meter.value = value;
    meter.setAttribute("aria-label", metric + " heuristic score");
    item.append(label, score, meter); scoreItems.appendChild(item);
  });
"""
        text = text.replace(js_anchor, js_anchor + "\n" + score_js, 1)
    if 'id="profile-averages"' not in text:
        ledger_anchor = '        <div class="lbl" style="margin:18px 0 6px">By lands in hand</div>'
        assert ledger_anchor in text, "ledger table header not found"
        profile_html = """        <div class="lbl" style="margin:18px 0 4px">Average opening-hand profile</div>
        <div class="foot" id="profile-count">No scored hands yet</div>
        <div class="score-grid" id="profile-averages"></div>
"""
        text = text.replace(ledger_anchor, profile_html + ledger_anchor, 1)
        save_anchor = "  rows.push({l:lands, u:userKeep?1:0, r:rk?1:0, w:worked?1:0});"
        assert save_anchor in text, "ledger save line not found"
        text = text.replace(
            save_anchor,
            "  rows.push({l:lands, u:userKeep?1:0, r:rk?1:0, w:worked?1:0, p:handScores});",
            1)
        render_anchor = "  const d = deck;"
        assert render_anchor in text, "ledger render tail not found"
        render_js = """  const profiled = rows.filter(r=>r.p);
  $("#profile-count").textContent = profiled.length
    ? profiled.length + " scored hands · averages for this deck"
    : "No scored hands yet";
  const profileAverages = $("#profile-averages"); profileAverages.innerHTML = "";
  const metrics = ["velocity","consistency","interaction","efficiency","lethality"];
  if (profiled.length) metrics.forEach(metric => {
    const mean = Math.round(profiled.reduce((sum,row)=>sum+row.p[metric],0)/profiled.length);
    const item = document.createElement("div"); item.className = "score-item";
    const label = document.createElement("span"); label.textContent = metric;
    const score = document.createElement("b"); score.textContent = mean + "/100";
    const meter = document.createElement("progress"); meter.max = 100; meter.value = mean;
    meter.setAttribute("aria-label", "Average " + metric + " heuristic score");
    item.append(label, score, meter); profileAverages.appendChild(item);
  });
"""
        text = text.replace(render_anchor, render_js + render_anchor, 1)
    return text

# 1. swap DECKS payload
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
old_decks_js = txt[start:end]
new_decks_js = json.dumps(new_decks, separators=(",", ":"))
txt = txt[:start] + new_decks_js + txt[end:]

# Once the assembled trainer has been copied to PlayByPlay, refresh its two
# generated regions directly; the original-template substitutions below are
# intentionally one-time upgrades.
if "const ruleKeepStandard" in txt:
    rule_start = txt.find("// Hares v2 rule")
    rule_end = txt.find("const drawsByT4 = () =>", rule_start)
    assert rule_start >= 0 and rule_end >= 0, "generated rule region not found"
    txt = txt[:rule_start] + snippet + "\n" + txt[rule_end:]
    old_standard_footer = (
        'Base rule: <b>keep 2&ndash;5 lands, mulligan 0, 1, 6 or 7</b>. '
        'Standard PG/PH: <b>keep 2&ndash;5 only with a turn-1/2 board starter and at least 2 spells castable by turn 3</b>; '
        'Hares v2 also checks stranded payoffs, land bridges, and functional lands.')
    new_standard_footer = (
        'Base rule: <b>keep 2&ndash;5 lands, mulligan 0, 1, 6 or 7</b>. '
        'Standard PG/PH: <b>keep 2&ndash;5 only with a turn-1/2 board starter and at least 2 spells with mana value 3 or less</b> '
        '(Ethereal Armor counts only with a creature in hand); '
        'Hares v2 also checks stranded payoffs, land bridges, and functional lands.')
    if old_standard_footer in txt:
        txt = txt.replace(old_standard_footer, new_standard_footer, 1)
    else:
        assert new_standard_footer in txt, "generated rule footer not found"
    txt = add_hand_score_ui(txt)
    with open(os.path.join(ROOT, "mulligan-drill-v2.html"), "w", encoding="utf-8") as fh:
        fh.write(txt)
    print("refreshed mulligan-drill-v2.html from the deployed trainer, len", len(txt))
    raise SystemExit(0)

# 2. swap rule line for snippet
old_rule = "const ruleKeep = n => n>=2 && n<=5;"
assert old_rule in txt, "rule line not found"
txt = txt.replace(old_rule, snippet, 1)

# 3a. storage key bump v2 -> v3 (fresh ledger for new rule)
txt = txt.replace('mullDrill.v2.', 'mullDrill.v3.')

# 3b. deal(): card chrome = role + kind icons, kind-colored border, role badge.
# Mentor of the Meek (creature doing spell-things) reads 📖 not spell clothes;
# Hares keep a green engine outline; lands keep --land border + green ring.
old_tag = 'el.querySelector(".tag").textContent = c.l ? "Land" : (c.c + " mana");'
assert old_tag in txt, "deal tag line not found"
new_tag = ('el.querySelector(".tag").textContent = (c.ri ? c.ri + " " : "") + (c.l ? ((c.t && c.t.includes("half")) ? "½ Land" : "Land") : (c.m || (c.c + " mana")));\n'
           '    el.querySelector(".nm").textContent = (c.ki ? c.ki + " " : "") + c.n;\n'
           '    if (c.y) el.title = c.y + (c.m ? "  " + c.m : "") + (c.r ? "  [" + c.r + "]" : "");\n'
           '    if (c.r) { const b = document.createElement("div"); b.className = "role"; b.textContent = c.r; el.appendChild(b); }\n'
           '    const kindBorder = {land:"var(--land)",creature:"var(--keep)",artifact:"#8A6A1F",enchantment:"#7E5AA7",instant:"#C2543A",sorcery:"#C2543A",planeswalker:"#B8860B"}[c.k];\n'
           '    if (kindBorder) el.style.borderLeft = "4px solid " + kindBorder;\n'
           '    if (c.t && c.t.includes("bridge")) el.style.boxShadow = "inset 0 0 0 2px var(--keep)";\n'
           '    if (c.t && c.t.includes("stranded")) el.style.boxShadow = "inset 0 0 0 2px var(--mull)";\n'
           '    if (c.n === "Hare Apparent") el.style.outline = "2px solid var(--keep)";\n'
           '    if (c.t && c.t.includes("half")) { el.classList.add("half"); el.style.outline = "2px dashed var(--half)"; el.style.outlineOffset = "1px"; }')
txt = txt.replace(old_tag, new_tag, 1)

# 3b2. role badge + legend CSS
old_css = '.card.land .tag{color:var(--land)}'
assert old_css in txt, "card css not found"
new_css = ('.card.land .tag{color:var(--land)}\n'
           '  .role{font-family:var(--mono);font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-top:2px}\n'
           '  .legend{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;font-size:12px;color:var(--muted)}\n'
           '  .legend span{font-family:var(--mono);font-size:11px;padding:2px 8px;border:1px solid var(--line);border-radius:999px;background:var(--surface-2)}\n'
           '  .card.half .tag{color:var(--half);font-weight:700}')
txt = txt.replace(old_css, new_css, 1)

# 3b2b. --half warning amber for half-lands: light root once; the two dark
# roots (prefers-color-scheme + [data-theme="dark"]) must both get it, so
# replace the dark block without a count limit.
old_half_l = '--land:#8A6A1F; --land-bg:#F6EFDD; --shadow:'
assert old_half_l in txt, "light land vars not found"
txt = txt.replace(old_half_l, '--land:#8A6A1F; --land-bg:#F6EFDD; --half:#B45309; --shadow:', 1)
old_half_d = '--land:#CBA451; --land-bg:#2A2417; --shadow:'
assert old_half_d in txt, "dark land vars not found"
txt = txt.replace(old_half_d, '--land:#CBA451; --land-bg:#2A2417; --half:#E8A33D; --shadow:')

# 3b3. legend line directly under the hand (before the call controls)
old_call = '<div class="call">'
assert old_call in txt, "call div not found"
legend = ('<div class="legend" aria-label="Card face legend">'
          '<span>🐇 hare/engine</span><span>🌉 land-bridge</span>'
          '<span>📖 draw</span><span>🔥 removal</span><span>🛡️ protect</span>'
          '<span>💥 payoff</span><span>💧 ramp</span><span>👯 tokens</span>'
          '<span>🧰 utility</span><span>🟫 land</span><span>⚠️ ½ land — counts 0.5</span>'
          '<span>⚙️ artifact</span><span>✨ enchantment</span>'
          '<span>⚡ instant</span><span>🔮 sorcery</span><span>👑 planeswalker</span>'
          '</div>\n<div class="call">')
txt = txt.replace(old_call, legend, 1)

# 3c. call(): use ruleWhy(hand) instead of ruleKeep(lands); add reason pill
old_rk = "  const lands = hand.filter(c=>c.l).length;\n  const rk = ruleKeep(lands);"
assert old_rk in txt, "call rk lines not found"
new_rk = ("  const lands = hand.filter(c=>c.l).length;\n"
          "  const why = (typeof ruleWhy === \"function\") ? ruleWhy(hand) : {keep: ruleKeep(hand), why: \"\"};\n"
          "  const rk = why.keep;")
txt = txt.replace(old_rk, new_rk, 1)

old_pills = '  pill("Rule: " + (rk ? "keep" : "mulligan"), rk?"ok":"no");'
assert old_pills in txt, "rule pill not found"
new_pills = ('  pill("Rule: " + (rk ? "keep" : "mulligan"), rk?"ok":"no");\n'
             '  if (why.why) pill(why.why);')
txt = txt.replace(old_pills, new_pills, 1)

# 3c2. verdict pill: surface the functional count when it differs from the raw
# land count (half-lands): "2 lands in hand -- 1.5 functional".
old_lands_pill = '  pill(lands + " lands in hand");'
assert old_lands_pill in txt, "lands pill not found"
new_lands_pill = ('  const fv = hand.reduce((s,c)=>s+landVal(c),0);\n'
                  '  pill(lands + " lands in hand" + (fv !== lands ? " -- " + fv + " functional" : ""));')
txt = txt.replace(old_lands_pill, new_lands_pill, 1)

# 3c3. hand-panel counter: functional count visible BEFORE the call -- the
# whole point of the nitpick (he mulled before any verdict could warn him).
old_hc = '$("#handcount").textContent = hand.filter(c=>c.l).length + " lands · " + (7-hand.filter(c=>c.l).length) + " spells";'
assert old_hc in txt, "handcount line not found"
new_hc = ('const lv = hand.filter(c=>c.l).length, fv = hand.reduce((s,c)=>s+landVal(c),0);\n'
          '  $("#handcount").textContent = lv + " lands" + (fv !== lv ? " (" + fv + " functional)" : "") + " · " + (7-lv) + " spells";')
txt = txt.replace(old_hc, new_hc, 1)

# 3d. default-select the new Standard PG target entry
old_sel = 'const hares = DECKS.findIndex(d=>d.id==="brawl100-elspeth-hares");'
assert old_sel in txt, "default select not found"
txt = txt.replace(old_sel, 'const hares = DECKS.findIndex(d=>d.id==="standard60-porcelain-gallery-v1-target");', 1)

# 3d2. show concise display labels without changing persistent deck IDs
old_option = 'o.textContent = d.cmdr ? d.id + "  ·  " + d.cmdr : d.id;'
assert old_option in txt, "deck selector option line not found"
txt = txt.replace(old_option, 'o.textContent = d.label || (d.cmdr ? d.id + "  ·  " + d.cmdr : d.id);', 1)

# 3e. footer rule text: mention v2 bridge rule
old_foot = 'The rule: <b>keep 2&ndash;5 lands, mulligan 0, 1, 6 or 7.</b>'
assert old_foot in txt, "footer not found"
new_foot = ('Base rule: <b>keep 2&ndash;5 lands, mulligan 0, 1, 6 or 7</b>. '
            'Standard PG/PH: <b>keep 2&ndash;5 only with a turn-1/2 board starter and at least 2 spells with mana value 3 or less</b> '
            '(Ethereal Armor counts only with a creature in hand); '
            'Hares v2 also checks stranded payoffs, land bridges, and functional lands.')
txt = txt.replace(old_foot, new_foot, 1)

# 3f. verdict notes: score the CALL (agree with rule), not the draw luck.
# The draws panel shows what WOULD have happened, but a 1-lander that spikes
# two lands is a bad keep that got lucky, not a mulligan mistake.
old_notes = """  let msg;
  if(userKeep && !worked && landsT4 < 3) msg = "That keep would have stalled on " + landsT4 + " lands. This is the shape the rule is trying to save you from.";
  else if(userKeep && !worked) msg = "That keep would have flooded — " + landsT4 + " lands by turn four.";
  else if(userKeep && worked) msg = "Good keep. " + landsT4 + " lands by turn four is exactly the working range.";
  else if(!userKeep && worked) msg = "That hand would have worked — " + landsT4 + " lands by turn four. Worth remembering next time the instinct fires.";
  else msg = "Right call. That hand would have ended on " + landsT4 + " lands by turn four.";"""
assert old_notes in txt, "verdict notes not found"
new_notes = """  const agreed = (userKeep === rk);
  let msg;
  if(userKeep && !worked && landsT4 < 3) msg = "That keep stalled on " + landsT4 + " lands. This is the shape the rule is trying to save you from." + (agreed ? "" : " (You disagreed with the rule here — the ledger's agreement score is what matters, not this one draw.)");
  else if(userKeep && !worked) msg = "That keep flooded — " + landsT4 + " lands by turn four." + (agreed ? "" : " (You disagreed with the rule here.)");
  else if(userKeep && worked && agreed) msg = "Good keep, and the draws cooperated: " + landsT4 + " lands by turn four is the working range.";
  else if(userKeep && worked && !agreed) msg = "Lucky, not right: the rule mulls this hand and " + landsT4 + " lands by turn four doesn't change that. You kept against the rule and got bailed out by draws — the agreement score keeps you honest here.";
  else if(!userKeep && worked && agreed) msg = "Right mull — the rule agrees. It would have drawn to " + landsT4 + " lands, but a 1-lander needs two topdecks to function and most don't get there. Process over outcome.";
  else if(!userKeep && worked && !agreed) msg = "You mulled a hand the rule keeps, and it would have drawn to " + landsT4 + " lands. Worth reviewing — but one draw doesn't overturn the rule.";
  else msg = "Right call. That hand would have ended on " + landsT4 + " lands by turn four.";"""
txt = txt.replace(old_notes, new_notes, 1)

txt = add_hand_score_ui(txt)

open(os.path.join(ROOT, "mulligan-drill-v2.html"), "w", encoding="utf-8").write(txt)
print("wrote mulligan-drill-v2.html, len", len(txt))
