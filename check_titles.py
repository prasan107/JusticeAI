import json

with open('data/processed/judgments_clean.json', encoding='utf-8') as f:
    cases = json.load(f)

no_title = [c for c in cases if not c.get('title') or c.get('title') == 'Unknown Case']
print(f"Unknown titles: {len(no_title)} / {len(cases)}")
print()
for c in no_title[:5]:
    print(c.get('full_text', '')[:300])
    print('---')