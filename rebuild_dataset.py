import pandas as pd
import json
import re

INPUT_CSV  = "data/raw/cases.csv"
OUTPUT_JSON = "data/processed/judgments_clean.json"

df = pd.read_csv(INPUT_CSV)
print(f"Loaded {len(df)} cases from cases.csv")
print(f"Columns: {df.columns.tolist()}")

# ── Detect case type from act/headnote/text ──
def detect_case_type(row):
    text = " ".join([
        str(row.get("act", "")),
        str(row.get("headnote", "")),
        str(row.get("judgment_text", ""))[:500],
    ]).lower()

    if any(kw in text for kw in ["bail", "criminal appeal", "ipc", "crpc", "murder",
                                  "rape", "robbery", "theft", "accused", "fir",
                                  "section 302", "section 307", "section 376",
                                  "criminal appellate"]):
        return "Criminal"
    if any(kw in text for kw in ["writ petition", "article 32", "article 226",
                                  "fundamental right", "constitution", "constitutional"]):
        return "Constitutional"
    if any(kw in text for kw in ["civil appeal", "civil appellate", "contract",
                                  "property", "compensation", "damages", "decree",
                                  "special leave petition", "slp"]):
        return "Civil"
    return "Civil"  # default

# ── Detect court from judgment text ──
def detect_court(text):
    t = (text or "").upper()
    if "SUPREME COURT OF INDIA" in t:
        return "Supreme Court of India"
    if "HIGH COURT" in t:
        return "High Court"
    if "SESSIONS COURT" in t:
        return "Sessions Court"
    return "Supreme Court of India"

# ── Extract year from date_of_judgment or text ──
def extract_year(row):
    date_str = str(row.get("date_of_judgment", ""))
    m = re.search(r"\b(19|20)\d{2}\b", date_str)
    if m:
        return int(m.group())
    # Try from case ID
    case_id = str(row.get("id", ""))
    m2 = re.search(r"\b(20\d{2})\b", case_id)
    if m2:
        return int(m2.group())
    return 2020

# ── Outcome detection from judgment text ──
RULES = {
    "Appeal Allowed":   ["appeal allowed", "petition allowed", "appeal is allowed",
                         "allowed accordingly", "quashed and set aside", "reversed",
                         "appeals are allowed"],
    "Appeal Dismissed": ["appeal dismissed", "petition dismissed", "appeal is dismissed",
                         "dismissed accordingly", "appeals are dismissed"],
    "Bail Granted":     ["bail granted", "bail is granted", "released on bail",
                         "bail allowed", "grant of bail"],
    "Acquitted":        ["acquitted", "not guilty", "acquittal", "benefit of doubt"],
    "Convicted":        ["convicted", "found guilty", "sentenced to imprisonment",
                         "upheld the conviction", "conviction upheld", "conviction confirmed"],
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

# ── Build records ──
records = []
for i, row in df.iterrows():
    petitioner = str(row.get("petitioner", "")).strip()
    respondent = str(row.get("respondent", "")).strip()
    full_text  = str(row.get("judgment_text", "") or row.get("raw_text", "")).strip()

    # Build clean title from structured columns
    if petitioner and respondent and petitioner != "nan" and respondent != "nan":
        title = f"{petitioner} vs {respondent}"
    else:
        title = "Unknown Case"

    case_type = detect_case_type(row)
    court     = detect_court(full_text)
    year      = extract_year(row)
    outcome   = detect_outcome(full_text)

    records.append({
        "case_id":   f"csv_{i}",
        "title":     title,
        "court":     court,
        "year":      year,
        "case_type": case_type,
        "full_text": full_text,
        "outcome":   outcome,
        "source":    "csv",
    })

# ── Stats ──
total     = len(records)
labeled   = sum(1 for r in records if r["outcome"])
outcomes  = {}
for r in records:
    if r["outcome"]:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1
case_types = {}
for r in records:
    ct = r["case_type"]
    case_types[ct] = case_types.get(ct, 0) + 1

print(f"\nTotal records: {total}")
print(f"Labeled with outcome: {labeled}")
print(f"\nOutcome distribution:")
for k, v in sorted(outcomes.items(), key=lambda x: -x[1]):
    print(f"  {v}  {k}")
print(f"\nCase type distribution:")
for k, v in sorted(case_types.items(), key=lambda x: -x[1]):
    print(f"  {v}  {k}")

print(f"\nSample titles:")
for r in records[:5]:
    print(f"  {r['title']}")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"\n✅ Saved {total} records to {OUTPUT_JSON}")