import io
p = io.open('scripts/deck_check.py', encoding='utf-8').read()
a = 'if \"competitivebrawl\" in self.cache[key]:'
b = 'if \"competitivebrawl\" in self.cache[key] and \"standardbrawl\" in self.cache[key]:'
assert a in p, 'guard not found'
p = p.replace(a, b)
c = 'if fmt == \"brawl\" and commander_ci is not None:'
d = 'if fmt in (\"brawl\", \"standardbrawl\") and commander_ci is not None:'
assert c in p, 'ci guard not found'
p = p.replace(c, d)
io.open('scripts/deck_check.py', 'w', encoding='utf-8', newline='').write(p)
print('patched ok')
