# ml_pipeline/train.py
# Module 2 — Train with SMOTE balancing + multiple models
# Run from project root: python ml_pipeline/train.py

import pandas as pd
import numpy as np
import pickle
import os
import json
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix, issparse
import xgboost as xgb

DATA_PATH       = "data/labeled/cases_labeled.csv"
CLEAN_DATA_PATH = "data/processed/judgments_clean.json"
MODELS_DIR      = "ml_pipeline/saved_models"
os.makedirs(MODELS_DIR, exist_ok=True)

def load_data():
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} labeled cases")
    if os.path.exists(CLEAN_DATA_PATH):
        with open(CLEAN_DATA_PATH, encoding="utf-8") as f:
            clean = json.load(f)
        text_map = {str(c["case_id"]): c.get("full_text", "") for c in clean}
        df["full_text"] = df["case_id"].astype(str).map(text_map).fillna("")
    else:
        df["full_text"] = ""
    df["text_combined"] = df["title"].fillna("") + " " + df["full_text"].str[:500]
    return df

def train():
    df = load_data()
    df = df.dropna(subset=["outcome", "case_type", "court", "year"])
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(2000).astype(int)

    # Keep outcomes with 10+ samples
    counts = df["outcome"].value_counts()
    df = df[df["outcome"].isin(counts[counts >= 10].index)].reset_index(drop=True)
    print(f"After filtering: {len(df)} cases")
    print("\nOutcome distribution:")
    print(df["outcome"].value_counts().to_string())

    # Encode
    le_court   = LabelEncoder()
    le_type    = LabelEncoder()
    le_outcome = LabelEncoder()
    df["court_enc"]   = le_court.fit_transform(df["court"].astype(str))
    df["type_enc"]    = le_type.fit_transform(df["case_type"].astype(str))
    df["outcome_enc"] = le_outcome.fit_transform(df["outcome"].astype(str))

    # Features
    struct = csr_matrix(df[["court_enc", "type_enc", "year"]].values.astype(float))
    tfidf  = TfidfVectorizer(max_features=500, ngram_range=(1, 2),
                             stop_words="english", min_df=2)
    text_f = tfidf.fit_transform(df["text_combined"].fillna(""))
    X = hstack([struct, text_f])
    y = df["outcome_enc"].values

    print(f"\nFeature matrix: {X.shape[0]} x {X.shape[1]}")
    print(f"Classes: {list(le_outcome.classes_)}")

    # Try SMOTE for balancing
    smote_available = False
    try:
        from imblearn.over_sampling import SMOTE
        X_dense = X.toarray()
        sm = SMOTE(random_state=42, k_neighbors=3)
        X_bal, y_bal = sm.fit_resample(X_dense, y)
        print(f"\nSMOTE applied: {len(y)} → {len(y_bal)} samples")
        print("Balanced distribution:")
        for cls, count in zip(le_outcome.classes_, np.bincount(y_bal)):
            print(f"  {cls:<22}: {count}")
        smote_available = True
    except ImportError:
        print("\nSMOTE not available. Installing...")
        os.system("pip install imbalanced-learn -q")
        try:
            from imblearn.over_sampling import SMOTE
            X_dense = X.toarray()
            sm = SMOTE(random_state=42, k_neighbors=3)
            X_bal, y_bal = sm.fit_resample(X_dense, y)
            print(f"SMOTE applied: {len(y)} → {len(y_bal)} samples")
            smote_available = True
        except Exception as e:
            print(f"SMOTE failed: {e}. Using original data.")
            X_bal, y_bal = X.toarray(), y

    X_train, X_test, y_train, y_test = train_test_split(
        X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal
    )
    print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")

    results = {}

    # ── Logistic Regression ────────────────────────────────────
    print("\n" + "="*55)
    print("Training Logistic Regression...")
    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42, C=1.0)
    lr.fit(X_train, y_train)
    lr_acc = accuracy_score(y_test, lr.predict(X_test))
    print(f"Logistic Regression Accuracy: {lr_acc*100:.1f}%")
    print(classification_report(y_test, lr.predict(X_test),
                                target_names=le_outcome.classes_, zero_division=0))
    results["Logistic Regression"] = (lr_acc, lr)

    # ── Random Forest ──────────────────────────────────────────
    print("="*55)
    print("Training Random Forest...")
    rf = RandomForestClassifier(n_estimators=300, max_depth=15,
                                min_samples_split=3, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_acc = accuracy_score(y_test, rf.predict(X_test))
    print(f"Random Forest Accuracy: {rf_acc*100:.1f}%")
    print(classification_report(y_test, rf.predict(X_test),
                                target_names=le_outcome.classes_, zero_division=0))
    results["Random Forest"] = (rf_acc, rf)

    # ── XGBoost ────────────────────────────────────────────────
    print("="*55)
    print("Training XGBoost...")
    xgb_model = xgb.XGBClassifier(n_estimators=300, max_depth=6,
                                   learning_rate=0.05, subsample=0.8,
                                   colsample_bytree=0.8, random_state=42,
                                   eval_metric="mlogloss", verbosity=0)
    xgb_model.fit(X_train, y_train)
    xgb_acc = accuracy_score(y_test, xgb_model.predict(X_test))
    print(f"XGBoost Accuracy: {xgb_acc*100:.1f}%")
    print(classification_report(y_test, xgb_model.predict(X_test),
                                target_names=le_outcome.classes_, zero_division=0))
    results["XGBoost"] = (xgb_acc, xgb_model)

    # ── Pick best ──────────────────────────────────────────────
    best_name = max(results, key=lambda k: results[k][0])
    best_acc, best_model = results[best_name]
    cv_scores = cross_val_score(best_model, X_bal, y_bal, cv=5, scoring="accuracy")

    print("="*55)
    print(f"\n MODEL COMPARISON")
    for name, (acc, _) in sorted(results.items(), key=lambda x: -x[1][0]):
        marker = " <-- BEST" if name == best_name else ""
        print(f"  {name:<25}: {acc*100:.1f}%{marker}")
    print(f"\nBest model: {best_name}")
    print(f"  Test accuracy:      {best_acc*100:.1f}%")
    print(f"  5-fold CV accuracy: {cv_scores.mean()*100:.1f}% +/- {cv_scores.std()*100:.1f}%")
    if smote_available:
        print(f"  SMOTE balancing:    Yes")

    # ── Save ───────────────────────────────────────────────────
    with open(f"{MODELS_DIR}/random_forest.pkl", "wb") as f:
        pickle.dump(rf, f)
    with open(f"{MODELS_DIR}/xgboost.pkl", "wb") as f:
        pickle.dump(xgb_model, f)
    with open(f"{MODELS_DIR}/logistic_regression.pkl", "wb") as f:
        pickle.dump(lr, f)
    with open(f"{MODELS_DIR}/tfidf.pkl", "wb") as f:
        pickle.dump(tfidf, f)
    with open(f"{MODELS_DIR}/encoders.pkl", "wb") as f:
        pickle.dump({
            "court":         le_court,
            "type":          le_type,
            "outcome":       le_outcome,
            "best_model":    best_name,
            "test_accuracy": round(best_acc, 4),
            "cv_accuracy":   round(cv_scores.mean(), 4),
            "smote_used":    smote_available,
        }, f)

    print(f"\nAll models saved to {MODELS_DIR}/")
    print("\nDone! Next step: build the predict API endpoint.")

if __name__ == "__main__":
    train()
