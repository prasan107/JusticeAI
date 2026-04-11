import json

with open('data/processed/judgments_clean.json', encoding='utf-8') as f:
    cases = json.load(f)

for i in [2, 3, 4, 7]:
    title = cases[i].get('title', '')
    text = cases[i].get('full_text', '')[:500]
    print(f"=== Case {i} | title: {title} ===")
    print(repr(text))
    print()