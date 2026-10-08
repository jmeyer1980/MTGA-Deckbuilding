"""Inspect mulligan-drill.html structure + pool.json fields for the drill upgrade."""
import json, re

DRILL = r"C:\Users\jerio\MTGA_PlayByPlay\mulligan-drill.html"
txt = open(DRILL, encoding="utf-8").read()
print("=== drill len:", len(txt))

print("=== function names:")
for m in re.finditer(r"function\s+(\w+)", txt):
    print("  ", m.group(1))

print("=== const/let top-level:")
for m in re.finditer(r"^(?:const|let|var)\s+(\w+)", txt, re.M):
    print("  ", m.group(1))

i = txt.find("const DECKS")
print("=== DECKS block starts at", i)
decks = json.loads(txt[i + len("const DECKS = "):txt.find("];", i) + 1]) if False else None
# parse DECKS array manually: find matching close
start = txt.find("const DECKS = ") + len("const DECKS = ")
depth = 0
instr = False
esc = False
for j in range(start, len(txt)):
    ch = txt[j]
    if instr:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            instr = False
    else:
        if ch == '"':
            instr = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
decks = json.loads(txt[start:end])
print("=== deck count:", len(decks))
for d in decks:
    print("  ", d.get("id"), "size", d.get("size"), "lands", d.get("lands"),
          "cmdr", d.get("cmdr"), "ncards", len(d.get("cards", [])))
print("=== sample card entry:", json.dumps(decks[0]["cards"][0]))

# rule logic: print script section between deck data end and </script>
rest = txt[end:end + 20000]
print("=== script-after-decks (first 6000 chars):")
print(rest[:6000])
