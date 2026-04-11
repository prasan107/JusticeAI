# build_dataset.py
# Combines all data sources into one clean labeled dataset
# Run from: C:\Users\ADMIN\Downloads\justiceai

import json, re, os
import pandas as pd
from collections import Counter
from random import shuffle, seed
seed(42)

# ── Paths ──────────────────────────────────────────────────────
CSV_PATH      = r"data\raw\cases.csv"
JUDIPL_PATH   = r"data\raw\case_files_total.csv"
ENRICHED_PATH = r"data\raw\judgments_enriched.json"
OUT_PATH      = r"data\processed\judgments_clean.json"

# ── Helpers ────────────────────────────────────────────────────
def extract_year(text):
    if not text: return 2015
    m = re.findall(r'\b(19[5-9]\d|20[0-2]\d)\b', str(text)[:500])
    return int(m[0]) if m else 2015

def extract_court(text):
    if not text: return "Supreme Court of India"
    t = text.lower()[:500]
    if "supreme court" in t:    return "Supreme Court of India"
    if "high court" in t:       return "High Court"
    if "sessions court" in t:   return "Sessions Court"
    if "district court" in t:   return "District Court"
    if "tribunal" in t:         return "Tribunal"
    return "Supreme Court of India"

def classify_type(case_cat, case_type_col, text):
    cat = str(case_cat).lower()
    typ = str(case_type_col).lower()
    if "criminal" in cat: return "Criminal"
    if "civil"    in cat: return "Civil"
    if isinstance(text, str):
        t = text.lower()[:300]
        if any(k in t for k in ["bail","ipc","accused","murder","fir","criminal"]):
            return "Criminal"
    return "Civil"

# ── Strict keyword rules (last 300 chars of judgment text) ─────
TAIL_RULES = {
    "Bail Granted":     ["bail is granted","bail granted","released on bail",
                         "bail application is allowed","bail application allowed"],
    "Bail Rejected":    ["bail is rejected","bail refused","bail denied",
                         "bail application is dismissed","bail application dismissed"],
    "Convicted":        ["convicted and sentenced","found guilty and sentenced",
                         "sentenced to rigorous imprisonment","sentenced to life imprisonment",
                         "hereby convicted"],
    "Acquitted":        ["accused is acquitted","hereby acquitted",
                         "acquitted of all charges","acquitted of the charges",
                         "benefit of doubt and acquitted"],
    "Appeal Allowed":   ["appeal is allowed","appeal allowed","appeal is hereby allowed",
                         "impugned order is set aside","impugned judgment is set aside",
                         "order of the high court is set aside"],
    "Appeal Dismissed": ["appeal is dismissed","appeal dismissed","appeal is hereby dismissed",
                         "high court order is upheld","order of the high court is upheld"],
}

def label_from_tail(text):
    if not text or not isinstance(text, str): return None
    tail = text[-300:].lower()
    for outcome, keywords in TAIL_RULES.items():
        if any(kw in tail for kw in keywords):
            return outcome
    return None

# ══════════════════════════════════════════════════════════════
# SOURCE 1: cases.csv (500 structured cases — clean labels)
# ══════════════════════════════════════════════════════════════
print("=" * 55)
print("SOURCE 1: cases.csv")
cases_csv = []
try:
    df_csv = pd.read_csv(CSV_PATH, encoding="utf-8", on_bad_lines="skip")
    print(f"  Loaded {len(df_csv)} rows")
    print(f"  Columns: {df_csv.columns.tolist()}")

    OUTCOME_REMAP = {
        "Convicted":        "Convicted",
        "Acquitted":        "Acquitted",
        "Bail Granted":     "Bail Granted",
        "Bail Rejected":    "Bail Rejected",
        "Appeal Allowed":   "Appeal Allowed",
        "Partly Allowed":   "Appeal Allowed",
        "Appeal Dismissed": "Appeal Dismissed",
    }

    # Try outcome column variants
    outcome_col = None
    for c in ["outcome","Outcome","label","Label","result","Result"]:
        if c in df_csv.columns:
            outcome_col = c
            break

    text_col = None
    for c in ["judgment_text","full_text","text","judgement","headnote"]:
        if c in df_csv.columns:
            text_col = c
            break

    print(f"  Outcome col: {outcome_col}, Text col: {text_col}")

    for idx, row in df_csv.iterrows():
        outcome = OUTCOME_REMAP.get(str(row.get(outcome_col, "")).strip()) if outcome_col else None
        text = str(row.get(text_col, "")) if text_col else ""

        if not outcome:
            outcome = label_from_tail(text)
        if not outcome:
            continue

        petitioner = str(row.get("petitioner", row.get("Petitioner", "")))
        respondent = str(row.get("respondent", row.get("Respondent", "")))
        title = f"{petitioner} vs {respondent}".strip(" vs")
        if title == " vs " or not title.strip():
            title = f"Case_{idx}"

        cases_csv.append({
            "case_id":   f"csv_{idx}",
            "title":     title[:200],
            "court":     extract_court(text) if text else str(row.get("court","Supreme Court of India")),
            "year":      extract_year(text) if text else int(str(row.get("year",2015))[:4]),
            "case_type": classify_type(row.get("case_type",""), "", text),
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "csv",
        })

    print(f"  Labeled: {len(cases_csv)}")
    for k,v in Counter(c["outcome"] for c in cases_csv).most_common():
        print(f"    {v:4d}  {k}")
except Exception as e:
    print(f"  ERROR: {e}")

# ══════════════════════════════════════════════════════════════
# SOURCE 2: Jud-IPL (53k Supreme Court cases)
# ══════════════════════════════════════════════════════════════
print("\nSOURCE 2: Jud-IPL (case_files_total.csv)")
judipl_cases = []
try:
    df_jud = pd.read_csv(JUDIPL_PATH, encoding="utf-8", on_bad_lines="skip")
    print(f"  Loaded {len(df_jud)} rows")

    # case_type → outcome mapping (only high-confidence types)
    JUDIPL_MAP = {
        ("appeal",                 "Accepted"): "Appeal Allowed",
        ("appeal",                 "Rejected"): "Appeal Dismissed",
        ("writ petition",          "Accepted"): "Appeal Allowed",
        ("writ petition",          "Rejected"): "Appeal Dismissed",
        ("special leave petition", "Accepted"): "Appeal Allowed",
        ("special leave petition", "Rejected"): "Appeal Dismissed",
        ("arbitration appeal",     "Accepted"): "Appeal Allowed",
        ("arbitration appeal",     "Rejected"): "Appeal Dismissed",
    }

    for idx, row in df_jud.iterrows():
        label     = str(row.get("label", "")).strip()
        case_type = str(row.get("case_type", "")).strip().lower()
        case_cat  = str(row.get("case_category", "")).strip().lower()

        if label == "Other":
            continue

        outcome = JUDIPL_MAP.get((case_type, label))
        if not outcome:
            continue

        text = str(row.get("judgement","") or row.get("proof_sentence","") or "")
        if len(text) < 200:
            continue

        name = str(row.get("name", f"Case_{idx}"))
        judipl_cases.append({
            "case_id":   f"judipl_{idx}",
            "title":     name[:200],
            "court":     "Supreme Court of India",
            "year":      extract_year(text),
            "case_type": "Criminal" if case_cat == "criminal" else "Civil",
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "judipl",
        })

    print(f"  Labeled: {len(judipl_cases)}")
    for k,v in Counter(c["outcome"] for c in judipl_cases).most_common():
        print(f"    {v:4d}  {k}")

    # Balance: cap Appeal Allowed and Appeal Dismissed at 3000 each
    allowed   = [c for c in judipl_cases if c["outcome"] == "Appeal Allowed"]
    dismissed = [c for c in judipl_cases if c["outcome"] == "Appeal Dismissed"]
    shuffle(allowed);   allowed   = allowed[:3000]
    shuffle(dismissed); dismissed = dismissed[:3000]
    judipl_cases = allowed + dismissed
    print(f"  After balancing cap: {len(judipl_cases)}")

except Exception as e:
    print(f"  ERROR: {e}")

# ══════════════════════════════════════════════════════════════
# SOURCE 3: judgments_enriched.json (scraped + text fetched)
# ══════════════════════════════════════════════════════════════
print("\nSOURCE 3: judgments_enriched.json")
enriched_cases = []
try:
    with open(ENRICHED_PATH, encoding="utf-8") as f:
        enriched = json.load(f)
    print(f"  Loaded {len(enriched)} records")

    for r in enriched:
        text = r.get("full_text","") or ""
        if not text or text.strip() in ("Full Document",""):
            continue
        if len(text) < 300:
            continue

        outcome = label_from_tail(text)
        if not outcome:
            continue

        enriched_cases.append({
            "case_id":   f"scraped_{r.get('case_id','')}",
            "title":     r.get("title","Unknown")[:200],
            "court":     r.get("court") or extract_court(text),
            "year":      r.get("year") or extract_year(text),
            "case_type": r.get("case_type") or classify_type("","",text),
            "full_text": text[:8000],
            "url":       r.get("url",""),
            "outcome":   outcome,
            "source":    "scraped",
        })

    print(f"  Labeled: {len(enriched_cases)}")
    for k,v in Counter(c["outcome"] for c in enriched_cases).most_common():
        print(f"    {v:4d}  {k}")

except Exception as e:
    print(f"  ERROR: {e}")

# ══════════════════════════════════════════════════════════════
# MERGE & DEDUPLICATE
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 55)
print("MERGING ALL SOURCES...")

all_cases = cases_csv + judipl_cases + enriched_cases

# Deduplicate by title
seen_titles = set()
deduped = []
for c in all_cases:
    key = c["title"].lower().strip()[:80]
    if key not in seen_titles:
        seen_titles.add(key)
        deduped.append(c)

print(f"Before dedup: {len(all_cases)}")
print(f"After dedup:  {len(deduped)}")

labeled = [c for c in deduped if c.get("outcome")]
print(f"\nFinal labeled cases: {len(labeled)}")
print("\nFinal outcome distribution:")
for k,v in Counter(c["outcome"] for c in labeled).most_common():
    print(f"  {v:5d}  {k}")

print("\nSource breakdown:")
for k,v in Counter(c["source"] for c in labeled).most_common():
    print(f"  {v:5d}  {k}")

# Save
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(deduped)} total records to {OUT_PATH}")
print("\nNext steps:")
print("  1. python restore_and_retrain.py")
print("  2. Remove-Item -Recurse -Force chroma_store")
print("  3. python scripts/ingest_to_vectordb.py")