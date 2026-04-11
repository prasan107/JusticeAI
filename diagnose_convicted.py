import json
import numpy as np
from collections import Counter

DATA_PATH = "data/processed/judgments_clean.json"

KEYWORD_GROUPS = {
    "kw_convicted":        ["convicted", "found guilty", "sentenced", "imprisonment", "conviction"],
    "kw_acquitted":        ["acquitted", "not guilty", "acquittal", "benefit of doubt"],
    "kw_bail":             ["bail granted", "bail is granted", "released on bail", "bail allowed"],
    "kw_appeal_allowed":   ["appeal allowed", "set aside", "quashed", "reversed"],
    "kw_appeal_dismissed": ["appeal dismissed", "dismissed accordingly"],
    "kw_ipc":              ["ipc", "indian penal code", "section 302", "section 307", "section 420"],
    "kw_civil":            ["civil appeal", "special leave petition", "writ petition"],
    "kw_murder":           ["murder", "culpable homicide", "section 302"],
}

def check_keywords(text):
    t = (text or "").lower()
    return {k: int(any(kw in t for kw in kws)) for k, kws in KEYWORD_GROUPS.items()}

with open(DATA_PATH, encoding="utf-8") as f:
    records = json.load(f)

labeled = [r for r in records if r.get("outcome") and r["outcome"] != "None"]

# For each outcome, show average keyword feature values
outcomes = ["Convicted", "Appeal Allowed", "Bail Granted", "Acquitted"]
print("── Average keyword feature values by outcome ──")
print(f"{'Feature':<25}", end="")
for o in outcomes:
    print(f"{o[:12]:>14}", end="")
print()
print("-" * 81)

all_kw_names = list(KEYWORD_GROUPS.keys())
for kw_name in all_kw_names:
    print(f"{kw_name:<25}", end="")
    for outcome in outcomes:
        cases = [r for r in labeled if r.get("outcome") == outcome]
        avg = np.mean([check_keywords(r.get("full_text",""))[kw_name] for r in cases])
        print(f"{avg:>14.2f}", end="")
    print()

print("\n── case_type distribution per outcome ──")
for outcome in outcomes:
    cases = [r for r in labeled if r.get("outcome") == outcome]
    types = Counter(r.get("case_type", "Unknown") for r in cases)
    print(f"\n{outcome} ({len(cases)} cases):")
    for t, c in types.most_common():
        print(f"  {t}: {c}")

# Check: how many Convicted cases have kw_convicted = 1?
convicted = [r for r in labeled if r.get("outcome") == "Convicted"]
kw_hit = sum(1 for r in convicted if check_keywords(r.get("full_text",""))["kw_convicted"])
print(f"\n── Convicted cases with kw_convicted=1: {kw_hit}/{len(convicted)} ({100*kw_hit/len(convicted):.1f}%) ──")

# What ELSE has kw_convicted=1?
print("\n── All outcomes where kw_convicted=1 ──")
for outcome in set(r["outcome"] for r in labeled):
    cases = [r for r in labeled if r.get("outcome") == outcome]
    hit = sum(1 for r in cases if check_keywords(r.get("full_text",""))["kw_convicted"])
    print(f"  {outcome}: {hit}/{len(cases)}")