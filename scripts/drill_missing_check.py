"""Why do Ambitious Farmhand + Plains miss pool.json?"""
import json, os, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pool = json.load(open(os.path.join(ROOT, "pool.json"), encoding="utf-8"))
P = pool.get("pool", pool)
def norm(n):
    d = unicodedata.normalize("NFKD", n)
    return "".join(c for c in d if not unicodedata.combining(c)).casefold()
print("Ambitious in P:", "Ambitious Farmhand" in P)
print("Plains in P:", "Plains" in P)
cands = [k for k in P if norm(k).startswith("ambitious") or norm(k) == "plains"]
print("cands:", cands[:10])
# collection lines?
hits = [l.rstrip() for l in open(os.path.join(ROOT, "collection.txt"), encoding="utf-8") if "armbitious" in l.lower() or "ambitious" in l.lower() or l.strip().lower().endswith(" plains")]
print("collection hits:", hits[:10])
allplains = [l.rstrip() for l in open(os.path.join(ROOT, "collection.txt"), encoding="utf-8") if norm(l.split(None,1)[1] if len(l.split(None,1))>1 else "") == "plains"]
print("n plains lines:", len(allplains), allplains[:5])
