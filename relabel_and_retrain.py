import json, pickle, os
import numpy as np
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import pandas as pd

DATA_PATH  = os.path.join("data", "processed", "judgments_clean.json")
MODELS_DIR = os.path.join("ml_pipeline", "saved_models")

# Now we have enough Acquitted cases to keep separate
# Merge only Partly Allowed into Appeal Allowed
OUTCOME_REMAP = {
    "Convicted":        "Convicted",
    "Acquitted":        "Acquitted",
    "Bail Granted":     "Bail Granted",
    "Bail Rejected":    "Bail Rejected",
    "Appeal Allowed":   "Appeal Allowed",
    "Partly Allowed":   "Appeal Allowed",
    "Appeal Dismissed": "Appeal Dismissed",
}

print("Loading data...")
with open(DATA_PATH, encoding="utf-8") as f:
    records = json.load(f)

print("Total records:", len(records))

rows = []
for r in records:
    raw_outcome = r.get("outcome", "")
    if not raw_outcome or raw_outcome == "None":
        continue
    mapped = OUTCOME_REMAP.get(raw_outcome)
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

print("Training samples:", len(rows))
df = pd.DataFrame(rows)

print("\nOutcome distribution:")
for k, v in df["outcome"].value_counts().items():
    print(f"  {v:4d}  {k}")

le_court   = LabelEncoder()
le_outcome = LabelEncoder()
df["court_enc"]   = le_court.fit_transform(df["court"].fillna("Unknown"))
df["outcome_enc"] = le_outcome.fit_transform(df["outcome"])

tfidf_head = TfidfVectorizer(max_features=150, ngram_range=(1,2))
tfidf_tail = TfidfVectorizer(max_features=200, ngram_range=(1,2))
head_feat = tfidf_head.fit_transform(df["head"]).toarray()
tail_feat = tfidf_tail.fit_transform(df["tail"]).toarray()
type_dummies = pd.get_dummies(df["case_type"].fillna("Unknown"), prefix="type").values

base = df[["court_enc", "year"]].values
X = np.hstack([base, type_dummies, head_feat, tail_feat])
y = df["outcome_enc"].values

print("\nFeature matrix:", X.shape)

min_class = min(Counter(y).values())
k = min(5, min_class - 1)
if k >= 1:
    sm = SMOTE(random_state=42, k_neighbors=k)
    X_bal, y_bal = sm.fit_resample(X, y)
    print("After SMOTE:", X_bal.shape[0], "samples")
else:
    X_bal, y_bal = X, y

for idx, cnt in sorted(Counter(y_bal).items()):
    print(f"  {le_outcome.classes_[idx]}: {cnt}")

X_train, X_test, y_train, y_test = train_test_split(X_bal, y_bal, test_size=0.2, random_state=42)

print("\nTraining XGBoost...")
xgb_model = xgb.XGBClassifier(
    n_estimators=300, max_depth=6, learning_rate=0.1,
    subsample=0.8, colsample_bytree=0.8,
    random_state=42, eval_metric="mlogloss",
)
xgb_model.fit(X_train, y_train)
xgb_preds = xgb_model.predict(X_test)
xgb_acc = (xgb_preds == y_test).mean()
print(f"XGBoost Accuracy: {round(xgb_acc * 100, 1)} %  (was 77.3%)")
print(classification_report(y_test, xgb_preds, target_names=le_outcome.classes_))

print("\nTraining Random Forest...")
rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_acc = (rf.predict(X_test) == y_test).mean()
print(f"Random Forest Accuracy: {round(rf_acc * 100, 1)} %")

os.makedirs(MODELS_DIR, exist_ok=True)
with open(os.path.join(MODELS_DIR, "xgboost.pkl"), "wb") as f:
    pickle.dump(xgb_model, f)
with open(os.path.join(MODELS_DIR, "random_forest.pkl"), "wb") as f:
    pickle.dump(rf, f)
with open(os.path.join(MODELS_DIR, "tfidf.pkl"), "wb") as f:
    pickle.dump({"head": tfidf_head, "tail": tfidf_tail}, f)
with open(os.path.join(MODELS_DIR, "encoders.pkl"), "wb") as f:
    pickle.dump({"court": le_court, "type": None, "outcome": le_outcome}, f)

type_cols = list(pd.get_dummies(df["case_type"].fillna("Unknown"), prefix="type").columns)
with open(os.path.join(MODELS_DIR, "type_columns.pkl"), "wb") as f:
    pickle.dump(type_cols, f)
with open(os.path.join(MODELS_DIR, "outcome_remap.pkl"), "wb") as f:
    pickle.dump(OUTCOME_REMAP, f)

print(f"\nFINAL: XGBoost {round(xgb_acc*100,1)}%  |  RF {round(rf_acc*100,1)}%")
print("All models saved. Restart uvicorn to use new models.")