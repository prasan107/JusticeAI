"""
Verifies and purifies outcome labels for scraped cases.
Shows the actual verdict tail for each criminal outcome so you can validate.
Also adds more specific criminal keywords to catch more verdicts.
Run from project root: python scripts/purify_labels.py
"""
import json, re
from pathlib import Path
from collections import Counter

DATA_PATH = Path("data/processed/judgments_clean.json")

# Enhanced rules with more Indian court verdict phrases
ENHANCED_RULES = {
    'Appeal Allowed': [
        'appeal is allowed', 'appeals are allowed', 'allowed accordingly',
        'stand allowed', 'impugned order is set aside', 'the appeal is allowed',
        'this appeal is allowed', 'impugned judgment is set aside',
        'impugned order is quashed', 'order is set aside', 'judgment is set aside',
        'appeal succeeds', 'we allow the appeal', 'appeals are hereby allowed',
    ],
    'Appeal Dismissed': [
        'appeal is dismissed', 'appeals are dismissed', 'dismissed accordingly',
        'stand dismissed', 'the appeal is dismissed', 'this appeal is dismissed',
        'appeal fails', 'we dismiss the appeal', 'appeals are hereby dismissed',
        'no merit in the appeal', 'find no merit',
    ],
    'Bail Granted': [
        'bail is granted', 'bail granted', 'released on bail',
        'directed to be released on bail', 'bail is hereby granted',
        'grant the bail', 'allow the bail', 'bail application is allowed',
        'release the applicant on bail', 'applicant is directed to be released',
        'enlarged on bail', 'we grant bail',
    ],
    'Bail Rejected': [
        'bail is rejected', 'bail application is dismissed', 'bail refused',
        'bail denied', 'bail application dismissed', 'reject the bail',
        'we reject the bail', 'bail application is rejected',
    ],
    'Acquitted': [
        'is acquitted', 'are acquitted', 'stand acquitted',
        'acquitted of all charges', 'acquitted of the charges',
        'acquitted of the offence', 'acquitted of all the charges',
        'set aside the conviction', 'conviction is set aside',
        'conviction and sentence is set aside', 'conviction and sentence are set aside',
        'accused is acquitted', 'appellant is acquitted',
        'acquit the appellant', 'acquit the accused',
        'we acquit', 'hereby acquitted',
    ],
    'Convicted': [
        'convicted and sentenced', 'found guilty and sentenced',
        'sentenced to rigorous imprisonment', 'sentenced to life imprisonment',
        'sentenced to imprisonment for life', 'conviction is confirmed',
        'conviction is upheld', 'upheld the conviction',
        'conviction and sentence is upheld', 'conviction and sentence are upheld',
        'conviction and sentence is confirmed', 'upheld the conviction and sentence',
        'sentence of life imprisonment is confirmed', 'guilty of the offence',
        'found to be guilty', 'we uphold the conviction',
        'outcome of judgment.*conviction',
    ],
    'Partly Allowed': [
        'partly allowed', 'partially allowed', 'allowed in part',
        'appeal is partly allowed', 'appeals are partly allowed',
        'partly succeeds', 'allowed to the extent',
    ],
}

def detect_outcome(text, tail_chars=1500):
    if not text:
        return None
    t = str(text).lower()
    tail = t[-tail_chars:]
    for outcome, keywords in ENHANCED_RULES.items():
        for kw in keywords:
            if re.search(kw, tail):
                return outcome
    return None

print("Loading dataset...")
with open(DATA_PATH, encoding='utf-8') as f:
    records = json.load(f)

print(f"Total records: {len(records)}")

# Re-label all records with enhanced rules
changed = 0
newly_found = 0
for r in records:
    old_outcome = r.get('outcome')
    new_outcome = None

    # For judipl records, trust the pre-assigned label
    if r.get('source') == 'judipl':
        continue

    # For csv and scraped, re-detect with enhanced rules
    new_outcome = detect_outcome(r.get('full_text', ''))

    if new_outcome != old_outcome:
        if old_outcome is None and new_outcome:
            newly_found += 1
        elif old_outcome and new_outcome:
            changed += 1
        r['outcome'] = new_outcome

print(f"Newly labeled: {newly_found}")
print(f"Re-labeled (changed): {changed}")

labeled = [r for r in records if r.get('outcome')]
dist = Counter(r['outcome'] for r in labeled)
print(f"\nUpdated outcome distribution ({len(labeled)} labeled):")
for k, v in dist.most_common():
    print(f"  {v:5d}  {k}")

# Show verdict tails for criminal cases to validate
print("\n" + "="*60)
print("VERIFICATION: Criminal case verdict tails")
print("="*60)

for outcome in ['Convicted', 'Acquitted', 'Bail Granted', 'Bail Rejected']:
    cases = [r for r in records
             if r.get('outcome') == outcome
             and r.get('source') in ('csv', 'scraped')]
    print(f"\n── {outcome} ({len(cases)} cases from csv/scraped) ──")
    for r in cases[:5]:
        tail = (r.get('full_text', '') or '')[-600:]
        print(f"\n  Title:  {r.get('title','')[:70]}")
        print(f"  Source: {r.get('source')} | Query: {r.get('search_query','N/A')[:40]}")
        print(f"  Tail:   {tail[-300:].strip()[:250]}")
        print()

# Save updated records
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved purified dataset: {len(records)} records, {len(labeled)} labeled")
print("\nNext steps:")
print("  python relabel_and_retrain.py")