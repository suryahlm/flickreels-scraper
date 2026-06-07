import json

with open('Scraping 01/30.01.2026/dramas.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

print(f'Total dramas scraped: {len(dramas)}')
print('\nDrama list:')
for i, (k, v) in enumerate(dramas.items()):
    eps = len(v.get('episodes', []))
    print(f"  {i+1}. {v['title']} ({k}) - {eps} eps")
