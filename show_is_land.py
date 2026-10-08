path = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\scripts\drill_build_v2.py"
txt = open(path, encoding="utf-8").read()
i = txt.find('def is_land')
print(txt[i:i+2600].replace('\\n', '\\n'))
