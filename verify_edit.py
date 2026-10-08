import json
base = r"C:\Users\jerio\MTGA_PlayByPlay"
for fname in ['gruul-pool.json', 'izzet-pool.json']:
    path = base + '\\' + fname
    with open(path, encoding='utf-8', errors='replace') as f:
        data = json.load(f)
    for item in data if isinstance(data, list) else []:
        if item.get('name') == 'Fabled Passage':
            print(fname, '->', json.dumps(item, ensure_ascii=False)[:400])
            break

# Confirm the rule script's landVal entry (surrounding context)
path2 = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\scripts\drill_rule_snippet.js"
txt = open(path2, encoding='utf-8').read()
i = txt.find('const landVal')
print('\n--- rule script landVal ---')
print(txt[i-100:i+420].replace('\\n', '\\n'))

# Confirm HALF edit context
path3 = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\scripts\drill_build_v2.py"
txt3 = open(path3, encoding='utf-8').read()
i3 = txt3.find('HALF = {')
print('\n--- drill_build_v2 HALF ---')
print(txt3[i3-150:i3+350].replace('\\n', ' '))
