# scripts/process_datasets.py
# Run from justiceai/ folder: python scripts/process_datasets.py

import json, csv, os, re
import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
LABELED_DIR = "data/labeled"
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(LABELED_DIR, exist_ok=True)

OUTCOME_RULES = {
    "Appeal Allowed":   ["appeal is allowed", "appeals are allowed", "appeal allowed",
                         "petition is allowed", "petition allowed", "allowed accordingly",
                         "set aside", "quashed and set aside", "reversed", "appeal partly allowed"],
    "Appeal Dismissed": ["appeal is dismissed", "appeals are dismissed", "appeal dismissed",
                         "petition is dismissed", "petition dismissed", "dismissed accordingly",
                         "upheld the conviction", "conviction upheld", "dismissed with costs"],
    "Acquitted":        ["acquitted", "not guilty", "discharged", "quash the criminal proceedings",
                         "quashed the chargesheet", "quashed and set aside the conviction"],
    "Convicted":        ["convicted", "found guilty", "sentenced to", "imprisonment for life",
                         "guilty of the offence", "conviction confirmed"],
    "Bail Granted":     ["bail is granted", "bail granted", "released on bail",
                         "grant of bail", "bail allowed", "interim bail"],
    "Bail Rejected":    ["bail is rejected", "bail rejected", "bail denied",
                         "bail refused", "bail application dismissed"],
    "Partly Allowed":   ["allowed in part", "partly allowed", "partially allowed",
                         "modified to the extent"],
}

# Auto-label from search query (for scraped cases with no full text)
QUERY_OUTCOME_MAP = {
    "acquittal": "Acquitted",
    "conviction": "Convicted",
    "bail application": "Bail Granted",
    "anticipatory bail": "Bail Granted",
}

def detect_outcome(text: str, search_query: str = "") -> str:
    if text and len(text) > 50:
        text_lower = text.lower()
        for outcome, keywords in OUTCOME_RULES.items():
            for kw in keywords:
                if kw in text_lower:
                    return outcome
    # Fallback: use search query for scraped cases
    if search_query:
        sq = search_query.lower()
        for kw, outcome in QUERY_OUTCOME_MAP.items():
            if kw in sq:
                return outcome
    return None

def extract_year(text: str, title: str = "") -> int:
    combined = title + " " + text[:500]
    matches = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', combined)
    return int(matches[0]) if matches else 2000

def extract_court(text: str, title: str = "") -> str:
    combined = (title + " " + text[:300]).lower()
    if "supreme court" in combined:
        return "Supreme Court of India"
    elif "high court" in combined:
        m = re.search(r'([\w\s]+high court)', combined)
        return m.group(0).title() if m else "High Court"
    elif "sessions" in combined:
        return "Sessions Court"
    elif "district" in combined:
        return "District Court"
    elif "tribunal" in combined:
        return "Tribunal"
    elif "magistrate" in combined:
        return "Magistrate Court"
    return "Unknown"

def classify_case_type(text: str, title: str = "", query: str = "") -> str:
    combined = (query + " " + title + " " + text[:300]).lower()
    scores = {
        "Criminal": sum(1 for kw in ["ipc", "criminal", "accused", "conviction", "acquittal",
                        "bail", "fir", "offence", "murder", "theft", "rape", "fraud",
                        "cheating", "bribery", "corruption", "kidnapping", "dowry"] if kw in combined),
        "Civil":    sum(1 for kw in ["civil", "property", "contract", "compensation",
                        "plaintiff", "defendant", "land", "motor accident", "consumer",
                        "labour", "employment", "damages"] if kw in combined),
        "Family":   sum(1 for kw in ["divorce", "maintenance", "custody", "matrimonial",
                        "domestic violence", "hindu marriage", "adoption"] if kw in combined),
        "Constitutional": sum(1 for kw in ["article 14", "article 19", "article 21",
                        "fundamental right", "writ petition", "constitutional"] if kw in combined),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"

# ── PROCESS CSV ──────────────────────────────
def process_csv():
    csv_path = os.path.join(RAW_DIR, "cases.csv")
    if not os.path.exists(csv_path):
        print("cases.csv not found, skipping...")
        return []

    print("Processing cases.csv...")
    cases = []

    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(csv_path, encoding=enc, on_bad_lines="skip")
            break
        except Exception:
            continue

    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Rows: {len(df)}")

    # Use judgment_text as primary, raw_text as fallback
    for idx, row in df.iterrows():
        try:
            # Pick best text column
            full_text = ""
            for col in ["judgment_text", "raw_text", "headnote"]:
                val = str(row.get(col, "")).strip()
                if len(val) > 200:
                    full_text = val
                    break

            if len(full_text) < 100:
                continue

            # Build title from petitioner/respondent
            petitioner = str(row.get("petitioner", "")).strip()[:80]
            respondent = str(row.get("respondent", "")).strip()[:80]
            title = f"{petitioner} vs {respondent}" if petitioner and respondent else f"Case {idx}"

            court = extract_court(full_text, title)
            year_raw = str(row.get("date_of_judgment", "")).strip()
            year = int(year_raw[:4]) if year_raw and year_raw[:4].isdigit() else extract_year(full_text)
            case_type = classify_case_type(full_text, title)
            outcome = detect_outcome(full_text)

            cases.append({
                "case_id": f"csv_{idx}",
                "title": title,
                "court": court,
                "year": year,
                "case_type": case_type,
                "full_text": full_text[:3000],
                "outcome": outcome,
                "source": "csv"
            })
        except Exception:
            continue

    print(f"  ✅ Processed {len(cases)} cases from CSV")
    return cases

# ── PROCESS JSON ─────────────────────────────
def process_json():
    json_path = os.path.join(RAW_DIR, "judgments_raw.json")
    if not os.path.exists(json_path):
        print("judgments_raw.json not found, skipping...")
        return []

    print("\nProcessing judgments_raw.json...")
    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    cases = []
    for c in raw:
        try:
            title = c.get("title", "")
            full_text = c.get("full_text", "") or title
            query = c.get("search_query", "")

            court = c.get("court", "Unknown")
            if court == "Unknown":
                court = extract_court(full_text, title)

            year = c.get("year", 2000)
            if year == 2000:
                year = extract_year(full_text, title)

            case_type = classify_case_type(full_text, title, query)
            outcome = detect_outcome(full_text, query)

            cases.append({
                "case_id": c.get("case_id", f"json_{len(cases)}"),
                "title": title,
                "court": court,
                "year": year,
                "case_type": case_type,
                "full_text": full_text[:3000],
                "outcome": outcome,
                "source": "scraped"
            })
        except Exception:
            continue

    print(f"  ✅ Processed {len(cases)} cases from JSON")
    return cases

# ── MERGE AND SAVE ────────────────────────────
def merge_and_save(csv_cases, json_cases):
    # Deduplicate by case_id only (not title — titles can be similar but different cases)
    seen_ids = set()
    unique = []
    for c in csv_cases + json_cases:
        cid = str(c["case_id"])
        if cid not in seen_ids:
            seen_ids.add(cid)
            unique.append(c)

    print(f"\nTotal unique cases: {len(unique)}")

    # Save all for Module 1
    clean_path = os.path.join(PROCESSED_DIR, "judgments_clean.json")
    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(unique)} cases → {clean_path}")

    # Save labeled for Module 2
    labeled = [c for c in unique if c.get("outcome")]
    labeled_path = os.path.join(LABELED_DIR, "cases_labeled.csv")
    with open(labeled_path, "w", newline="", encoding="utf-8") as f:
        fields = ["case_id", "title", "court", "year", "case_type", "outcome", "source"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in labeled:
            w.writerow({k: c.get(k, "") for k in fields})
    print(f"✅ Saved {len(labeled)} labeled cases → {labeled_path}")

    # Summary
    print(f"\n{'='*50}")
    print(f"DATASET SUMMARY")
    print(f"{'='*50}")
    print(f"Total cases  (Module 1 - embeddings): {len(unique)}")
    print(f"Labeled cases (Module 2 - ML train):  {len(labeled)}")
    print(f"\nOutcome distribution:")
    oc = {}
    for c in labeled:
        oc[c["outcome"]] = oc.get(c["outcome"], 0) + 1
    for o, n in sorted(oc.items(), key=lambda x: -x[1]):
        print(f"  {o:<22}: {n}")
    print(f"\nCase type distribution:")
    tc = {}
    for c in unique:
        tc[c["case_type"]] = tc.get(c["case_type"], 0) + 1
    for t, n in sorted(tc.items(), key=lambda x: -x[1]):
        print(f"  {t:<22}: {n}")
    print(f"{'='*50}")

if __name__ == "__main__":
    csv_cases  = process_csv()
    json_cases = process_json()
    merge_and_save(csv_cases, json_cases)
    print("\n✅ Done! Next step: python scripts/ingest_to_vectordb.py")