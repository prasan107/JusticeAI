"""
Run this from project root to extract clean labeled cases from Jud-IPL dataset.
python scripts/extract_judipl.py
"""
import json, re
import pandas as pd
from pathlib import Path
from collections import Counter

CSV_PATH    = Path("data/raw/case_files_total.csv")
OUTPUT_PATH = Path("data/raw/judipl_extracted.json")

print(f"Loading {CSV_PATH} ...")
df = pd.read_csv(CSV_PATH)
print(f"Total rows: {len(df)}")

# Map case_type + case_category + label → outcome
def map_outcome(row):
    ct  = str(row.get("case_type", "")).lower()
    cc  = str(row.get("case_category", "")).lower()
    lbl = str(row.get("label", "")).lower()

    if lbl == "other":
        return None

    accepted = lbl == "accepted"
    rejected = lbl == "rejected"

    # Only map appeal and SLP — most reliable
    if "appeal" in ct or "special leave" in ct:
        if cc == "criminal":
            return "Appeal Allowed" if accepted else "Appeal Dismissed"
        elif cc == "civil":
            return "Appeal Allowed" if accepted else "Appeal Dismissed"

    if "writ" in ct and cc == "civil":
        return "Appeal Allowed" if accepted else "Appeal Dismissed"

    return None

records = []
for i, row in df.iterrows():
    outcome = map_outcome(row)
    if not outcome:
        continue

    text = str(row.get("judgement", "") or "").strip()
    if len(text) < 200:
        continue

    name = str(row.get("name", "") or "").strip()
    title = name if name and name != "nan" else "Unknown Case"

    case_category = str(row.get("case_category", "")).lower()
    case_type = "Criminal" if case_category == "criminal" else "Civil"

    year_m = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', text[:500])
    year = int(year_m.group()) if year_m else 2020

    records.append({
        "case_id":   f"judipl_{i}",
        "title":     title[:120],
        "court":     "Supreme Court of India",
        "year":      year,
        "case_type": case_type,
        "full_text": text[:6000],
        "outcome":   outcome,
        "source":    "judipl",
    })

print(f"Extracted: {len(records)}")

# Balance: max 1500 per class
MAX_PER_CLASS = 1500
balanced = []
counts = Counter()
for r in records:
    if counts[r["outcome"]] < MAX_PER_CLASS:
        balanced.append(r)
        counts[r["outcome"]] += 1

print(f"After balancing: {len(balanced)}")
print("\nOutcome distribution:")
for k, v in Counter(r["outcome"] for r in balanced).most_common():
    print(f"  {v:5d}  {k}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(balanced, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved to {OUTPUT_PATH}")
print("Now run: python scripts/final_merge.py")