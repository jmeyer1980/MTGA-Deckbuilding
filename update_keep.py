#!/usr/bin/env python3
"""Update KEEP tuple in pool.py to include oracle_text, keywords, produced_mana"""

with open('scripts/pool.py', 'r') as f:
    content = f.read()

old = 'KEEP = ("mana_cost", "cmc", "rarity", "type_line", "color_identity", "set")'
new = 'KEEP = ("mana_cost", "cmc", "rarity", "type_line", "color_identity", "set", "oracle_text", "keywords", "produced_mana")'

if old in content:
    content = content.replace(old, new)
    with open('scripts/pool.py', 'w') as f:
        f.write(content)
    print('Successfully updated KEEP tuple')
else:
    print('Could not find KEEP tuple')
    print('Looking for similar patterns...')
    # Try to find the KEEP line
    for i, line in enumerate(content.split('\n')):
        if 'KEEP' in line and 'mana_cost' in line:
            print(f'Line {i+1}: {line.strip()}')