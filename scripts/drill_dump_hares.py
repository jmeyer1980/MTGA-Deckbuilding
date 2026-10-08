"""Dump current brawl100-elspeth-hares DECKS entry + parse live v21b list."""
import json, re
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
for d in decks:
    if d["id"] == "brawl100-elspeth-hares":
        print(json.dumps(d, indent=2)[:8000])
        print("NCARDS", len(d["cards"]))
        break
print("---- live v21b ----")
print(open(r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\decks\brawl100-elspeth-hares-v21b.txt", encoding="utf-8").read()[:3000])
