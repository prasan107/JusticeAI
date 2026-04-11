"""
Purifies judgments_enriched.json to extract reliable outcome labels.
Uses progressive tail lengths + structured field detection.
Run from project root: python scripts/purify_enriched.py
"""
import json, re
from pathlib import Path
from collections import Counter

ENRICHED_PATH = Path("data/raw/judgments_enriched.json")
OUTPUT_PATH   = Path("data/raw/enriched_labeled.json")

RULES = {
    'Appeal Allowed': [
        'appeal is allowed', 'appeals are allowed', 'allowed accordingly',
        'stand allowed', 'impugned order is set aside', 'the appeal is allowed',
        'this appeal is allowed', 'impugned judgment is set aside',
        'impugned order is quashed', 'order is set aside', 'judgment is set aside',
        'appeal succeeds', 'we allow the appeal', 'appeals are hereby allowed',
        'appeal is hereby allowed',
    ],
    'Appeal Dismissed': [
        'appeal is dismissed', 'appeals are dismissed', 'dismissed accordingly',
        'stand dismissed', 'the appeal is dismissed', 'this appeal is dismissed',
        'appeal fails', 'we dismiss the appeal', 'appeals are hereby dismissed',
        'no merit in the appeal', 'find no merit', 'appeal is hereby dismissed',
    ],
    'Bail Granted': [
        'bail is granted', 'bail granted', 'released on bail',
        'directed to be released on bail', 'bail is hereby granted',
        'grant the bail', 'allow the bail', 'bail application is allowed',
        'release the applicant on bail', 'applicant is directed to be released',
        'enlarged on bail', 'we grant bail', 'bail application allowed',
        'is released on bail', 'shall be released on bail',
    ],
    'Bail Rejected': [
        'bail is rejected', 'bail application is dismissed', 'bail refused',
        'bail denied', 'bail application dismissed', 'reject the bail',
        'we reject the bail', 'bail application is rejected',
        'bail application rejected',
    ],
    'Acquitted': [
        'is acquitted', 'are acquitted', 'stand acquitted',
        'acquitted of all charges', 'acquitted of the charges',
        'acquitted of the offence', 'acquitted of all the charges',
        'set aside the conviction', 'conviction is set aside',
        'conviction and sentence is set aside',
        'conviction and sentence are set aside',
        'accused is acquitted', 'appellant is acquitted',
        'acquit the appellant', 'acquit the accused',
        'we acquit', 'hereby acquitted', 'acquittal is confirmed',
    ],
    'Convicted': [
        'convicted and sentenced', 'found guilty and sentenced',
        'sentenced to rigorous imprisonment', 'sentenced to life imprisonment',
        'sentenced to imprisonment for life', 'conviction is confirmed',
        'conviction is upheld', 'upheld the conviction',
        'conviction and sentence is upheld',
        'conviction and sentence are upheld',
        'conviction and sentence is confirmed',
        'upheld the conviction and sentence',
        'sentence of life imprisonment is confirmed',
        'found to be guilty', 'we uphold the conviction',
        'outcome of judgment.*conviction',
    ],
    'Partly Allowed': [
        'partly allowed', 'partially allowed', 'allowed in part',
        'appeal is partly allowed', 'appeals are partly allowed',
        'partly succeeds', 'allowed to the extent',
    ],
}

def detect_outcome(text, tail_chars):
    if not text:
        return None
    t = str(text).lower()
    tail = t[-tail_chars:]
    for outcome, keywords in RULES.items():
        for kw in keywords:
            if re.search(kw, tail):
                return outcome
    return None

def detect_from_structured_fields(text):
    """Check for structured outcome fields that Indian Kanoon includes"""
    t = str(text).lower()
    # Indian Kanoon sometimes has "Outcome of judgment: Conviction" as a field
    m = re.search(r'outcome of judgment\s*[:\-]\s*(\w+)', t)
    if m:
        val = m.group(1).lower()
        if 'convict' in val:
            return 'Convicted'
        if 'acquit' in val:
            return 'Acquitted'
        if 'bail' in val:
            return 'Bail Granted'
        if 'allow' in val:
            return 'Appeal Allowed'
        if 'dismiss' in val:
            return 'Appeal Dismissed'

    # Check "disposed of" patterns
    if re.search(r'appeal.*disposed of.*allowed', t[-800:]):
        return 'Appeal Allowed'
    if re.search(r'appeal.*disposed of.*dismissed', t[-800:]):
        return 'Appeal Dismissed'

    return None

print("Loading enriched data...")
with open(ENRICHED_PATH, encoding='utf-8') as f:
    enriched = json.load(f)

print(f"Total records: {len(enriched)}")

results = []
method_counter = Counter()

for r in enriched:
    text = r.get('full_text', '') or ''
    outcome = None
    method = None

    # Method 1: Structured field detection (most reliable)
    outcome = detect_from_structured_fields(text)
    if outcome:
        method = 'structured_field'

    # Method 2: Last 800 chars (verdict section)
    if not outcome:
        outcome = detect_outcome(text, 800)
        if outcome:
            method = 'tail_800'

    # Method 3: Last 1500 chars
    if not outcome:
        outcome = detect_outcome(text, 1500)
        if outcome:
            method = 'tail_1500'

    # Method 4: Last 2500 chars (wider net, slightly less reliable)
    if not outcome:
        outcome = detect_outcome(text, 2500)
        if outcome:
            method = 'tail_2500'

    if outcome:
        method_counter[method] += 1
        results.append({**r, 'outcome': outcome, 'label_method': method})

print(f"\nLabeled: {len(results)}/{len(enriched)}")
print("\nOutcome distribution:")
dist = Counter(r['outcome'] for r in results)
for k, v in dist.most_common():
    print(f"  {v:4d}  {k}")

print("\nLabeling method breakdown:")
for k, v in method_counter.most_common():
    print(f"  {v:4d}  {k}")

# Show sample tails for verification
print("\n" + "="*60)
print("VERIFICATION SAMPLES")
print("="*60)
for outcome in ['Convicted', 'Acquitted', 'Bail Granted']:
    cases = [r for r in results if r['outcome'] == outcome]
    print(f"\n── {outcome} ({len(cases)} total) ──")
    for r in cases[:3]:
        tail = text[-500:] if (text := r.get('full_text','')) else ''
        print(f"  Title:  {r.get('title','')[:65]}")
        print(f"  Method: {r.get('label_method')} | Query: {r.get('search_query','')[:35]}")
        print(f"  Tail:   {tail[-250:].strip()[:220]}")
        print()

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ Saved {len(results)} labeled records to {OUTPUT_PATH}")
print("\nNow update scripts/final_merge.py to also load enriched_labeled.json")
print("Or run: python scripts/final_merge.py (it already loads judgments_enriched.json)")