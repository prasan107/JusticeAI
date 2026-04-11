# Auto-label judgment outcomes from raw text
# Run: python auto_label.py
import json, csv, re, os

INPUT_PATH = "../data/raw/judgments_raw.json"
OUTPUT_PATH = "../data/labeled/cases_labeled.csv"
os.makedirs("../data/labeled", exist_ok=True)

# Keyword rules to detect outcome
OUTCOME_RULES = {
    "Convicted":            ["convicted", "found guilty", "guilty of", "sentenced to"],
    "Acquitted":            ["acquitted", "not guilty", "discharged", "set aside conviction"],
    "Appeal Dismissed":     ["appeal dismissed", "petition dismissed", "dismissed"],
    "Appeal Allowed":       ["appeal allowed", "petition allowed", "allowed"],
    "Bail Granted":         ["bail granted", "released on bail"],
    "Bail Rejected":        ["bail rejected", "bail denied", "bail refused"],
}

def detect_outcome(text: str):
    text_lower = text.lower()
    for outcome, keywords in OUTCOME_RULES.items():
        for kw in keywords:
            if kw in text_lower:
                return outcome
    return None     # inconclusive — skip for training

def extract_features(case: dict, outcome: str):
    return {
        "case_id":      case.get("tid", ""),
        "title":        case.get("title", ""),
        "court":        case.get("docsource", "Unknown"),
        "year":         case.get("publishdate", "2000")[:4],
        "case_type":    "Criminal" if any(x in case.get("title","").lower() for x in ["ipc","murder","theft","assault"]) else "Civil",
        "accused_count": 1,    # default; enhance later
        "outcome":      outcome,
    }

def run_labeling():
    with open(INPUT_PATH) as f:
        cases = json.load(f)

    labeled = []
    skipped = 0

    for case in cases:
        text = case.get("headline", "") + " " + case.get("title", "")
        outcome = detect_outcome(text)
        if outcome:
            labeled.append(extract_features(case, outcome))
        else:
            skipped += 1

    print(f"Labeled: {len(labeled)} | Skipped (inconclusive): {skipped}")

    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=labeled[0].keys())
        writer.writeheader()
        writer.writerows(labeled)

    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    run_labeling()
