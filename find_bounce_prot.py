import json
pool = json.load(open('pool.json', encoding='utf-8'))['pool']
results = []
for name, c in pool.items():
    ot = c.get('oracle_text', '') or ''
    ot_l = ot.lower()
    if any(kw in ot_l for kw in ['phase out', 'can\'t be returned to hand', 'cannot be returned to hand', 'remain on the battlefield']):
        ci = c.get('color_identity', [])
        if not ci or ci == ['w'] or ci == ['W']:
            legal = c.get('standardbrawl') == 'legal' or c.get('competitivebrawl') == 'legal'
            results.append((name, c.get('mana_cost'), c.get('cmc'), c.get('type_line'), ot[:200], legal))
for r in sorted(results, key=lambda x: (not r[5], x[2], x[0])):
    legal_flag = 'LEGAL' if r[5] else 'NOT_LEGAL'
    print(f'{r[2]:.0f} {r[0]:<45} {r[1]:<12} {r[3]} [{legal_flag}]')
    print(f'    {r[4]}')
    print()
