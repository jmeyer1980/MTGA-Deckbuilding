import json

pool = json.load(open("pool.json", encoding="utf-8"))["pool"]

for name in [
    "Blossoming Sands",
    "Selesnya Guildgate",
    "Plains",
    "Forest",
    "Mountain",
    "Ojer Taq, Deepest Foundation",
    "Elder Mountain",
]:
    rec = pool.get(name)
    if rec:
        print(f"{name}: qty={rec.get('qty', 'N/A')}")
    else:
        print(f"{name}: NOT IN POOL")
