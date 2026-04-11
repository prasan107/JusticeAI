"""
final_merge.py — Combines ALL data sources into judgments_clean.json
Run from project root: python scripts/final_merge.py

Sources:
  1. data/raw/cases.csv              — 500 structured cases (clean labels)
  2. data/raw/judipl_extracted.json  — 3000 Jud-IPL appeal cases
  3. data/raw/indian_bail_judgments.csv — 1200 bail cases (736G/464R)
  4. data/raw/judgments_enriched.json   — 1774 scraped Indian Kanoon
  5. data/raw/enriched_labeled.json     — extra labeled scraped cases
"""

import json, re, os
import pandas as pd
from pathlib import Path
from collections import Counter

# ── Paths ──────────────────────────────────────────────────────
ROOT         = Path(".")
CSV_PATH     = ROOT / "data/raw/cases.csv"
JUDIPL_PATH  = ROOT / "data/raw/judipl_extracted.json"
BAIL_PATH    = ROOT / "data/raw/indian_bail_judgments.csv"
ENRICHED_PATH= ROOT / "data/raw/judgments_enriched.json"
LABELED_PATH = ROOT / "data/raw/enriched_labeled.json"
OUT_PATH     = ROOT / "data/processed/judgments_clean.json"

# ── Outcome remap for cases.csv labels ────────────────────────
OUTCOME_REMAP = {
    "Convicted":        "Convicted",
    "Acquitted":        "Acquitted",
    "Bail Granted":     "Bail Granted",
    "Bail Rejected":    "Bail Rejected",
    "Appeal Allowed":   "Appeal Allowed",
    "Partly Allowed":   "Appeal Allowed",
    "Appeal Dismissed": "Appeal Dismissed",
}

# ── Strict keyword rules (applied to last 1500 chars) ─────────
STRICT_RULES = {
    "Appeal Allowed":   ["appeal is allowed","appeals are allowed","the appeal is allowed",
                         "this appeal is allowed","allowed accordingly","stand allowed",
                         "impugned order is set aside","impugned judgment is set aside"],
    "Appeal Dismissed": ["appeal is dismissed","appeals are dismissed","the appeal is dismissed",
                         "this appeal is dismissed","dismissed accordingly","stand dismissed"],
    "Bail Granted":     ["bail is granted","bail granted","released on bail",
                         "directed to be released on bail","bail is hereby granted",
                         "bail application is allowed"],
    "Bail Rejected":    ["bail is rejected","bail application is dismissed",
                         "bail refused","bail denied","bail application dismissed"],
    "Acquitted":        ["is acquitted","are acquitted","stand acquitted",
                         "acquitted of all charges","acquitted of the offence",
                         "benefit of doubt","hereby acquitted"],
    "Convicted":        ["convicted and sentenced","found guilty and sentenced",
                         "sentenced to rigorous imprisonment","sentenced to life imprisonment",
                         "conviction is confirmed","conviction is upheld",
                         "upheld the conviction","hereby convicted"],
}

def detect_outcome(text):
    if not text or not isinstance(text, str): return None
    tail = text.lower()[-1500:]
    for outcome, keywords in STRICT_RULES.items():
        for kw in keywords:
            if kw in tail:
                return outcome
    return None

def extract_year(val):
    m = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', str(val)[:200])
    return int(m.group()) if m else 2015

def extract_court(text):
    if not text: return "Supreme Court of India"
    t = str(text).lower()[:500]
    if "supreme court" in t:  return "Supreme Court of India"
    if "high court"    in t:  return "High Court"
    if "sessions"      in t:  return "Sessions Court"
    if "district court"in t:  return "District Court"
    if "tribunal"      in t:  return "Tribunal"
    return "Supreme Court of India"

def classify_type(text):
    if not text: return "Civil"
    t = str(text).lower()[:500]
    if any(k in t for k in ["bail","ipc","accused","murder","rape",
                              "theft","robbery","fir","crpc","criminal"]):
        return "Criminal"
    if any(k in t for k in ["divorce","custody","maintenance","matrimonial"]):
        return "Family"
    if any(k in t for k in ["article 32","article 226","writ","fundamental right"]):
        return "Constitutional"
    return "Civil"

all_records = []
seen_ids    = set()
sep = "─" * 50

# ══════════════════════════════════════════════════
# SOURCE 1: cases.csv
# ══════════════════════════════════════════════════
print(sep)
print("SOURCE 1: cases.csv")
if CSV_PATH.exists():
    df = pd.read_csv(CSV_PATH, on_bad_lines="skip")
    print(f"  Loaded {len(df)} rows")
    added = 0
    for i, row in df.iterrows():
        cid = f"csv_{i}"
        if cid in seen_ids: continue
        text = str(row.get("judgment_text","") or row.get("raw_text","") or "").strip()
        if len(text) < 100: continue

        # Get outcome — from column first, then keyword detection
        raw_out = str(row.get("outcome","") or "").strip()
        outcome = OUTCOME_REMAP.get(raw_out) or detect_outcome(text)
        if not outcome: continue

        pet = str(row.get("petitioner","") or "").strip()
        res = str(row.get("respondent","") or "").strip()
        title = f"{pet} vs {res}".strip(" vs") if (pet and res and pet != "nan") else "Unknown"

        all_records.append({
            "case_id":   cid,
            "title":     title[:200],
            "court":     extract_court(text),
            "year":      extract_year(row.get("date_of_judgment","")),
            "case_type": classify_type(text),
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "csv",
        })
        seen_ids.add(cid)
        added += 1
    print(f"  Added: {added}")
    for k,v in Counter(r["outcome"] for r in all_records if r["source"]=="csv").most_common():
        print(f"    {v:4d}  {k}")
else:
    print("  ⚠️  Not found")

# ══════════════════════════════════════════════════
# SOURCE 2: judipl_extracted.json (pre-labeled)
# ══════════════════════════════════════════════════
print(sep)
print("SOURCE 2: judipl_extracted.json")
if JUDIPL_PATH.exists():
    with open(JUDIPL_PATH, encoding="utf-8") as f:
        judipl = json.load(f)
    print(f"  Loaded {len(judipl)} records")
    added = 0
    for r in judipl:
        cid = str(r.get("case_id",""))
        if cid in seen_ids: continue
        text = r.get("full_text","") or ""
        if len(text) < 100: continue
        outcome = r.get("outcome")
        if not outcome: continue
        all_records.append({
            "case_id":   cid,
            "title":     r.get("title","Unknown")[:200],
            "court":     r.get("court","Supreme Court of India"),
            "year":      r.get("year", 2015),
            "case_type": r.get("case_type","Civil"),
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "judipl",
        })
        seen_ids.add(cid)
        added += 1
    print(f"  Added: {added}")
    for k,v in Counter(r["outcome"] for r in all_records if r["source"]=="judipl").most_common():
        print(f"    {v:4d}  {k}")
else:
    print("  ⚠️  Not found — run extract_judipl.py first")

# ══════════════════════════════════════════════════
# SOURCE 3: indian_bail_judgments.csv
# ══════════════════════════════════════════════════
print(sep)
print("SOURCE 3: indian_bail_judgments.csv")
if BAIL_PATH.exists():
    df_bail = pd.read_csv(BAIL_PATH, on_bad_lines="skip")
    print(f"  Loaded {len(df_bail)} rows")
    added = 0
    for idx, row in df_bail.iterrows():
        cid = f"bail_{row.get('case_id', idx)}"
        if cid in seen_ids: continue
        outcome_raw = str(row.get("bail_outcome","")).strip()
        outcome = "Bail Granted" if outcome_raw == "Granted" else \
                  "Bail Rejected" if outcome_raw == "Rejected" else None
        if not outcome: continue

        facts   = str(row.get("facts","")           or "")
        reasons = str(row.get("judgment_reason","") or "")
        issues  = str(row.get("legal_issues","")    or "")
        summary = str(row.get("summary","")         or "")
        ipc     = str(row.get("ipc_sections","")    or "")
        crime   = str(row.get("crime_type","")      or "")
        text    = f"{facts} {issues} {reasons} {summary} IPC: {ipc} Crime: {crime}".strip()
        if len(text) < 100: continue

        all_records.append({
            "case_id":   cid,
            "title":     str(row.get("case_title","Unknown"))[:200],
            "court":     str(row.get("court","High Court")),
            "year":      extract_year(row.get("date","")),
            "case_type": "Criminal",
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "bail_dataset",
        })
        seen_ids.add(cid)
        added += 1
    print(f"  Added: {added}")
    for k,v in Counter(r["outcome"] for r in all_records if r["source"]=="bail_dataset").most_common():
        print(f"    {v:4d}  {k}")
else:
    print("  ⚠️  Not found")

# ══════════════════════════════════════════════════
# SOURCE 4: judgments_enriched.json
# ══════════════════════════════════════════════════
print(sep)
print("SOURCE 4: judgments_enriched.json")
if ENRICHED_PATH.exists():
    with open(ENRICHED_PATH, encoding="utf-8") as f:
        enriched = json.load(f)
    print(f"  Loaded {len(enriched)} records")
    added = 0
    for r in enriched:
        cid = str(r.get("case_id",""))
        if cid in seen_ids: continue
        text = r.get("full_text","") or ""
        if len(text) < 300: continue
        outcome = detect_outcome(text)
        if not outcome: continue
        all_records.append({
            "case_id":   cid,
            "title":     r.get("title","Unknown")[:200],
            "court":     r.get("court") or extract_court(text),
            "year":      r.get("year")  or extract_year(text),
            "case_type": r.get("case_type") or classify_type(text),
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "scraped",
        })
        seen_ids.add(cid)
        added += 1
    print(f"  Added: {added}")
    for k,v in Counter(r["outcome"] for r in all_records if r["source"]=="scraped").most_common():
        print(f"    {v:4d}  {k}")
else:
    print("  ⚠️  Not found")

# ══════════════════════════════════════════════════
# SOURCE 5: enriched_labeled.json
# ══════════════════════════════════════════════════
print(sep)
print("SOURCE 5: enriched_labeled.json")
if LABELED_PATH.exists():
    with open(LABELED_PATH, encoding="utf-8") as f:
        labeled_extra = json.load(f)
    print(f"  Loaded {len(labeled_extra)} records")
    added = 0
    for r in labeled_extra:
        cid = str(r.get("case_id","")) + "_lbl"
        if cid in seen_ids: continue
        text    = r.get("full_text","") or ""
        outcome = r.get("outcome") or detect_outcome(text)
        if not outcome or len(text) < 100: continue
        all_records.append({
            "case_id":   cid,
            "title":     r.get("title","Unknown")[:200],
            "court":     r.get("court") or extract_court(text),
            "year":      r.get("year")  or extract_year(text),
            "case_type": r.get("case_type") or classify_type(text),
            "full_text": text[:8000],
            "outcome":   outcome,
            "source":    "scraped_labeled",
        })
        seen_ids.add(cid)
        added += 1
    print(f"  Added: {added}")
    for k,v in Counter(r["outcome"] for r in all_records if r["source"]=="scraped_labeled").most_common():
        print(f"    {v:4d}  {k}")
else:
    print("  ⚠️  Not found — skipping")

# ══════════════════════════════════════════════════
# FINAL STATS & SAVE
# ══════════════════════════════════════════════════
print(sep)
labeled = [r for r in all_records if r.get("outcome")]
print(f"Total records : {len(all_records)}")
print(f"Labeled       : {len(labeled)}")

print("\nFinal outcome distribution:")
for k,v in Counter(r["outcome"] for r in labeled).most_common():
    print(f"  {v:5d}  {k}")

print("\nSource distribution:")
for k,v in Counter(r["source"] for r in all_records).most_common():
    print(f"  {v:5d}  {k}")

print("\nCase type distribution:")
for k,v in Counter(r["case_type"] for r in all_records).most_common():
    print(f"  {v:5d}  {k}")

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)
print(f"\n✅ Saved {len(all_records)} records to {OUT_PATH}")
print("\nNext steps:")
print("  python restore_and_retrain.py")
print("  Remove-Item -Recurse -Force chroma_store")
print("  python scripts/ingest_to_vectordb.py")