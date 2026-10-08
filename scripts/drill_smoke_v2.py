r"""Smoke-test the assembled v2 drill: registry totals, required hooks, and rule syntax."""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
print("decks:", len(decks))
hares = next(d for d in decks if d["id"] == "brawl100-elspeth-hares-v21c")
size = sum(c["q"] for c in hares["cards"])
lands = sum(c["q"] for c in hares["cards"] if c["l"])
print("hares size", size, "lands", lands, "rule", hares.get("rule"))
assert size == 99 and lands == 37, "totals wrong"  # 37: Ojer Taq is a TDFC creature, not a land (bug fix 2026-10-06)
emrakul = next(d for d in decks if d["id"] == "brawl100-emrakul-exigent-doom-v1b")
emrakul_size = sum(c["q"] for c in emrakul["cards"])
emrakul_lands = sum(c["q"] for c in emrakul["cards"] if c["l"])
assert emrakul["cmdr"] == "Emrakul, the Exigent Doom"
assert emrakul_size == emrakul["size"] == 99 and emrakul_lands == emrakul["lands"] == 40
assert next(c for c in emrakul["cards"] if c["n"] == "Wastes")["q"] == 28
treasure_map = next(c for c in emrakul["cards"] if c["n"].startswith("Treasure Map"))
assert not treasure_map["l"], "Treasure Map's front face is an artifact, not a land"
print("emrakul size", emrakul_size, "lands", emrakul_lands, "commander", emrakul["cmdr"])
for hook in ["ruleKeepV2", "ruleWhy", "isLandBridge", "mullDrill.v3.",
             "brawl100-elspeth-hares-v21c", "fail-mode", "Process over outcome",
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
# brace balance on the snippet region
i = txt.find("const landVal")
seg = txt[i:txt.find("</script", i)]
print("snippet braces:", seg.count("{"), seg.count("}"))
assert seg.count("{") == seg.count("}"), "brace mismatch"
print("SMOKE-OK")
