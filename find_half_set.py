path = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\scripts\drill_build_v2.py"
txt = open(path, encoding="utf-8").read()
for key in ['HALF = {', 'STRANDED = {', 'COLORLESS_RISK = {', 'BRIDGE = {']:
    i = txt.find(key)
    print('=== ', key, ' at', i)
    if i >= 0:
        seg = txt[i:i+450]
        print(seg.replace('\\n', ' '))
        print()
