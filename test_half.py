import json, sys
sys.path.insert(0, r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\scripts")
import drill_build_v2 as db

# Mimic pool records (izzet style, no type_line)
fab = {"name": "Fabled Passage", "n": "Fabled Passage", "i": "C", "t": ["Land"], "sub": "", "text": "..."}
print("is_land(Fabled Passage):", db.is_land(fab, "Fabled Passage"))

# Deck entry construction (same path as drill_build_v2)
e, key = db.pentry("Fabled Passage")
land = db.is_land(e, key)
print("pentry -> e:", e, "key:", key, "land:", land)

base = key.split(" // ")[0]
tags = []
if base in db.BRIDGE: tags.append("bridge")
if base in db.STRANDED or key in db.STRANDED: tags.append("stranded")
if base in db.HALF or key in db.HALF: tags.append("half")
print("tags:", tags)

entry = {"n": key, "q": 1, "l": land, "c": 0}
if tags: entry["t"] = tags
print("deck entry:", entry)

# Now run the rule snippet's landVal against the entry
# (load the snippet via exec in a sandboxed scope)
snippet = open(r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\scripts\drill_rule_snippet.js", encoding="utf-8").read()
ns = {}
exec(snippet, ns)
landVal = ns["landVal"]
print("landVal(Fabled Passage) ->", landVal(entry))
