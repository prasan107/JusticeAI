"""
Merges data/raw/judgments_enriched.json + data/raw/cases.csv
into data/processed/judgments_clean.json
Run after enrich_judgments.py completes.
"""
import json, re
import pandas as pd
from pathlib import Path

CSV_PATH      = Path("data/raw/cases.csv")
ENRICHED_PATH = Path("data/raw/judgments_enriched.json")
OUTPUT_PATH   = Path("data/processed/judgments_clean.json")

RULES = {
    "Appeal Allowed":   ["appeal allowed", "petition allowed", "allowed accordingly",
                         "quashed and set aside", "reversed", "appeals are allowed"],
    "Appeal Dismissed": ["appeal dismissed", "petition dismissed", "dismissed accordingly"],
    "Bail Granted":     ["bail granted", "bail is granted", "released on bail", "bail allowed"],
    "Bail Rejected":    ["bail rejected", "bail denied", "bail refused"],
    "Acquitted":        ["acquitted", "not guilty", "acquittal", "benefit of doubt"],
    "Convicted":        ["convicted", "found guilty", "sentenced to imprisonment",
                         "upheld the conviction", "conviction confirmed"],
    "Partly Allowed":   ["partly allowed", "partially allowed", "allowed in part"],
}

def detect_outcome(text):
    if not text:
        return None
    t = str(text).lower()
    tail = t[-600:]
    for outcome, keywords in RULES.items():
        for kw in keywords:
            if kw in tail:
                return outcome
    for outcome, keywords in RULES.items():
        for kw in keywords:
            if kw in t:
                return outcome
    return None

def detect_case_type(text, hint=""):
    t = (str(text) + " " + str(hint)).lower()
    if any(k in t for k in ["bail", "criminal appeal", "ipc", "crpc", "murder", "rape",
                              "robbery", "theft", "accused", "fir", "section 302",
                              "section 307", "section 376", "criminal appellate"]):
        return "Criminal"
    if any(k in t for k in ["article 32", "article 226", "fundamental right", "constitutional"]):
        return "Constitutional"
    if any(k in t for k in ["divorce", "custody", "maintenance", "domestic violence", "matrimonial"]):
        return "Family"
    return "Civil"

records = []

# ── Part 1: cases.csv (500 structured cases) ──
print("Loading cases.csv...")
df = pd.read_csv(CSV_PATH)
for i, row in df.iterrows():
    petitioner = str(row.get("petitioner", "")).strip()
    respondent = str(row.get("respondent", "")).strip()
    full_text  = str(row.get("judgment_text", "") or row.get("raw_text", "")).strip()

    title = f"{petitioner} vs {respondent}" if (
        petitioner and respondent and petitioner != "nan" and respondent != "nan"
    ) else "Unknown Case"

    year_m = re.search(r'\b(19|20)\d{2}\b', str(row.get("date_of_judgment", "")))
    year   = int(year_m.group()) if year_m else 2020

    court_text = full_text[:500].upper()
    if "SUPREME COURT OF INDIA" in court_text:
        court = "Supreme Court of India"
    elif "HIGH COURT" in court_text:
        court = "High Court"
    else:
        court = "Supreme Court of India"

    records.append({
        "case_id":   f"csv_{i}",
        "title":     title,
        "court":     court,
        "year":      year,
        "case_type": detect_case_type(full_text, row.get("act", "")),
        "full_text": full_text,
        "outcome":   detect_outcome(full_text),
        "source":    "csv",
    })

print(f"  Loaded {len(records)} CSV cases")

# ── Part 2: enriched scraped cases ──
if ENRICHED_PATH.exists():
    with open(ENRICHED_PATH, encoding="utf-8") as f:
        scraped = json.load(f)

    # Deduplicate by case_id vs existing
    existing_ids = {r["case_id"] for r in records}
    added = 0
    for r in scraped:
        if r["case_id"] in existing_ids:
            continue
        if not r.get("full_text") or r["full_text"] in ("Full Document", ""):
            continue
        if len(r.get("full_text", "")) < 200:
            continue

        r["outcome"]   = detect_outcome(r.get("full_text", ""))
        r["case_type"] = r.get("case_type") or detect_case_type(r.get("full_text", ""),
                                                                  r.get("search_query", ""))
        records.append(r)
        existing_ids.add(r["case_id"])
        added += 1

    print(f"  Added {added} scraped cases")
else:
    print("  No enriched file found — using CSV only")

# ── Stats ──
from collections import Counter
print(f"\nTotal records: {len(records)}")
labeled = [r for r in records if r.get("outcome")]
print(f"Labeled with outcome: {len(labeled)}")
print("\nOutcome distribution:")
for k, v in Counter(r["outcome"] for r in labeled).most_common():
    print(f"  {v}  {k}")
print("\nCase type distribution:")
for k, v in Counter(r.get("case_type", "Unknown") for r in records).most_common():
    print(f"  {v}  {k}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {len(records)} records to {OUTPUT_PATH}")