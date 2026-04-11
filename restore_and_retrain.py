# restore_and_retrain.py
# Run from: C:\Users\ADMIN\Downloads\justiceai

import json, pickle, os
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.over_sampling import SMOTE
import xgboost as xgb

MODELS_DIR = os.path.join("ml_pipeline", "saved_models")

print("Loading data...")
with open(r"data\processed\judgments_clean.json", encoding="utf-8") as f:
    all_records = json.load(f)

# Use ALL labeled records from all sources
labeled = [r for r in all_records
           if r.get("outcome") and r["outcome"] != "None"]
print(f"Total labeled records: {len(labeled)}")

OUTCOME_REMAP = {
    "Convicted":        "Convicted",
    "Acquitted":        "Acquitted",
    "Bail Granted":     "Bail Granted",
    "Bail Rejected":    "Bail Rejected",
    "Appeal Allowed":   "Appeal Allowed",
    "Partly Allowed":   "Appeal Allowed",   # merge — too few
    "Appeal Dismissed": "Appeal Dismissed",
}

rows = []
for r in labeled:
    mapped = OUTCOME_REMAP.get(r["outcome"])
    if not mapped:
        continue
    full = r.get("full_text", "") or ""
    rows.append({
        "court":     r.get("court", "Unknown"),
        "case_type": r.get("case_type", "Unknown"),
        "year":      int(str(r.get("year", 2015))[:4]),
        "head":      full[:300],
        "tail":      full[-600:],
        "outcome":   mapped,
    })

df = pd.DataFrame(rows)
print(f"\nTraining samples: {len(df)}")
print("\nOutcome distribution (real data):")
for k, v in df["outcome"].value_counts().items():
    print(f"  {v:5d}  {k}")

le_court   = LabelEncoder()
le_outcome = LabelEncoder()
df["court_enc"]   = le_court.fit_transform(df["court"].fillna("Unknown"))
df["outcome_enc"] = le_outcome.fit_transform(df["outcome"])

tfidf_head = TfidfVectorizer(max_features=150, ngram_range=(1,2))
tfidf_tail = TfidfVectorizer(max_features=200, ngram_range=(1,2))
head_feat    = tfidf_head.fit_transform(df["head"]).toarray()
tail_feat    = tfidf_tail.fit_transform(df["tail"]).toarray()
type_dummies = pd.get_dummies(df["case_type"].fillna("Unknown"), prefix="type").values
base         = df[["court_enc", "year"]].values
X = np.hstack([base, type_dummies, head_feat, tail_feat])
y = df["outcome_enc"].values

print(f"\nFeature matrix: {X.shape}")

# ── Capped SMOTE ───────────────────────────────────────────────
# Each minority class capped at 3x its real count
# Prevents over-synthetic inflation of small classes
counts    = Counter(y)
max_class = max(counts.values())

# Cap: minority classes → 3x real count, but not more than max class
sampling_strategy = {
    cls: min(cnt * 3, max_class)
    for cls, cnt in counts.items()
    if min(cnt * 3, max_class) > cnt
}

print("\nCapped SMOTE strategy:")
for cls_idx, target in sampling_strategy.items():
    real = counts[cls_idx]
    print(f"  {le_outcome.classes_[cls_idx]}: {real} real → {target} target "
          f"(+{target - real} synthetic)")

min_real = min(counts.values())
k_neighbors = min(5, min_real - 1)

if k_neighbors >= 1 and sampling_strategy:
    sm = SMOTE(random_state=42, k_neighbors=k_neighbors,
               sampling_strategy=sampling_strategy)
    X_bal, y_bal = sm.fit_resample(X, y)
    print(f"\nAfter capped SMOTE: {X_bal.shape[0]} samples")
else:
    X_bal, y_bal = X, y
    print("\nSMOTE skipped — classes already balanced")

print("\nClass counts after SMOTE:")
for idx, cnt in sorted(Counter(y_bal).items()):
    print(f"  {le_outcome.classes_[idx]}: {cnt}")

X_train, X_test, y_train, y_test = train_test_split(
    X_bal, y_bal, test_size=0.2, random_state=42)

print(f"\nTrain: {len(X_train)}  Test: {len(X_test)}")

# ── XGBoost ────────────────────────────────────────────────────
print("\nTraining XGBoost...")
xgb_model = xgb.XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.1,
    subsample=0.8, colsample_bytree=0.8,
    random_state=42, eval_metric="mlogloss",
)
xgb_model.fit(X_train, y_train)
xgb_preds = xgb_model.predict(X_test)
xgb_acc   = (xgb_preds == y_test).mean()
print(f"XGBoost Accuracy: {round(xgb_acc * 100, 1)}%")
print(classification_report(y_test, xgb_preds,
                             target_names=le_outcome.classes_))

# ── Random Forest ──────────────────────────────────────────────
print("Training Random Forest...")
rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_acc = (rf.predict(X_test) == y_test).mean()
print(f"Random Forest Accuracy: {round(rf_acc * 100, 1)}%")

# ── Save models ────────────────────────────────────────────────
os.makedirs(MODELS_DIR, exist_ok=True)
with open(os.path.join(MODELS_DIR, "xgboost.pkl"), "wb") as f:
    pickle.dump(xgb_model, f)
with open(os.path.join(MODELS_DIR, "random_forest.pkl"), "wb") as f:
    pickle.dump(rf, f)
with open(os.path.join(MODELS_DIR, "tfidf.pkl"), "wb") as f:
    pickle.dump({"head": tfidf_head, "tail": tfidf_tail}, f)
with open(os.path.join(MODELS_DIR, "encoders.pkl"), "wb") as f:
    pickle.dump({"court": le_court, "type": None, "outcome": le_outcome}, f)

type_cols = list(pd.get_dummies(
    df["case_type"].fillna("Unknown"), prefix="type").columns)
with open(os.path.join(MODELS_DIR, "type_columns.pkl"), "wb") as f:
    pickle.dump(type_cols, f)
with open(os.path.join(MODELS_DIR, "outcome_remap.pkl"), "wb") as f:
    pickle.dump(OUTCOME_REMAP, f)

print(f"\n{'='*50}")
print(f"FINAL: XGBoost {round(xgb_acc*100,1)}%  |  RF {round(rf_acc*100,1)}%")
print(f"6 classes: {', '.join(le_outcome.classes_)}")
print("Models saved. Run: cd backend && uvicorn main:app --reload")