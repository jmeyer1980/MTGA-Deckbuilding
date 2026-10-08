import os, glob
base = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding"
hits = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.ts') or f.endswith('.tsx') or f.endswith('.js') or f.endswith('.jsx'):
            p = os.path.join(root, f)
            try:
                txt = open(p, encoding='utf-8', errors='replace').read()
            except Exception:
                continue
            if 'Fabled Passage' in txt or ('Loyal Warhound' in txt and ('0.5' in txt or 'half' in txt.lower())):
                hits.append(p)
print('\n'.join(hits[:40]))
