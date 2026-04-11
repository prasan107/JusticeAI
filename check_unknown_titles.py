import json
import re

with open('data/processed/judgments_clean.json', encoding='utf-8') as f:
    cases = json.load(f)

# Find cases where stored title is missing or garbage
def is_clean_title(title):
    if not title or len(title.strip()) < 6:
        return False
    t = title.strip()
    garbage = re.compile(
        r'(Versus\s*\n|&\s*\n|\n\s*&|FIR\s*&|Sections\s*\d|'
        r'no\.\d|MBBS|NEET|CBSE|Contents\s*A\.|^nan|^Unknown$)',
        re.IGNORECASE
    )
    if garbage.search(t): return False
    if t.count('&') > 3: return False
    if t.count('\n') > 1: return False
    if len(t) > 200: return False
    return True

bad = [c for c in cases if not is_clean_title(c.get('title', ''))]
print(f"Bad/missing titles: {len(bad)} / {len(cases)}\n")

for c in bad[:20]:
    print(f"case_id : {c.get('case_id')}")
    print(f"title   : {repr(c.get('title', ''))}")
    print(f"text[:200]: {c.get('full_text', '')[:200]}")
    print("---")