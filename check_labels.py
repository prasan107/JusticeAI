import json
from collections import Counter

with open("data/processed/judgments_clean.json", encoding="utf-8") as f:
    records = json.load(f)

outcomes = Counter(r.get("outcome") for r in records if r.get("outcome"))
print("Outcome distribution:")
for k, v in outcomes.most_common():
    print(f"  {v}  {k}")

print("\n── 3 Convicted cases (last 300 chars) ──")
convicted = [r for r in records if r.get("outcome") == "Convicted"]
print(f"Total: {len(convicted)}")
for r in convicted[:3]:
    tail = (r.get("full_text") or "")[-300:]
    print(f"\nTitle: {r.get('title')}")
    print(f"Tail:  {tail[:250]}")

print("\n── 3 Acquitted cases (last 300 chars) ──")
acquitted = [r for r in records if r.get("outcome") == "Acquitted"]
print(f"Total: {len(acquitted)}")
for r in acquitted[:3]:
    tail = (r.get("full_text") or "")[-300:]
    print(f"\nTitle: {r.get('title')}")
    print(f"Tail:  {tail[:250]}")