# ml_pipeline/predictor.py
import pickle
import numpy as np
import os

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ml_pipeline", "saved_models")
_cache = {}

def _load():
    if _cache:
        return _cache
    with open(f"{MODELS_DIR}/xgboost.pkl", "rb") as f:
        _cache["model"] = pickle.load(f)
    with open(f"{MODELS_DIR}/tfidf.pkl", "rb") as f:
        tfidf = pickle.load(f)
        if isinstance(tfidf, dict):
            _cache["tfidf_head"] = tfidf["head"]
            _cache["tfidf_tail"] = tfidf["tail"]
        else:
            _cache["tfidf_head"] = tfidf
            _cache["tfidf_tail"] = tfidf
    with open(f"{MODELS_DIR}/encoders.pkl", "rb") as f:
        _cache["enc"] = pickle.load(f)
    with open(f"{MODELS_DIR}/type_columns.pkl", "rb") as f:
        _cache["type_cols"] = pickle.load(f)
    return _cache

DISPLAY_MAP = {
    "Acquitted":                   "Acquitted",
    "Appeal Allowed":              "Appeal Allowed",
    "Appeal Dismissed":            "Appeal Dismissed",
    "Bail Granted":                "Bail Granted",
    "Bail Rejected":               "Bail Rejected",
    "Convicted":                   "Convicted",
    "Civil - Appeal Allowed":      "Appeal Allowed",
    "Civil - Appeal Dismissed":    "Appeal Dismissed",
    "Criminal - Defence Wins":     "Acquitted / Bail Granted",
    "Criminal - Prosecution Wins": "Convicted",
    "Criminal Matter":             "Criminal Matter",
}

def predict_outcome(case_type: str, court: str, year: int, description: str = "") -> dict:
    art        = _load()
    model      = art["model"]
    tfidf_head = art["tfidf_head"]
    tfidf_tail = art["tfidf_tail"]
    enc        = art["enc"]
    type_cols  = art["type_cols"]
    le_court   = enc["court"]
    le_outcome = enc["outcome"]

    court_val = court if court in le_court.classes_ else le_court.classes_[0]
    court_enc = le_court.transform([court_val])[0]
    year_val  = int(year) if year else 2020

    type_key    = f"type_{case_type}"
    type_onehot = np.array([1 if col == type_key else 0 for col in type_cols], dtype=float)

    text          = description or f"{case_type} {court}"
    head_features = tfidf_head.transform([text]).toarray()[0]
    tail_features = tfidf_tail.transform([text]).toarray()[0]

    base = np.array([court_enc, year_val], dtype=float)
    X    = np.hstack([base, type_onehot, head_features, tail_features]).reshape(1, -1)

    proba      = model.predict_proba(X)[0]
    pred_idx   = int(np.argmax(proba))
    raw_pred   = le_outcome.inverse_transform([pred_idx])[0]
    confidence = float(proba[pred_idx])

    display_prediction = DISPLAY_MAP.get(raw_pred, raw_pred)

    all_outcomes = {
        DISPLAY_MAP.get(le_outcome.inverse_transform([i])[0],
                        le_outcome.inverse_transform([i])[0]): round(float(p), 4)
        for i, p in enumerate(proba)
    }

    return {
        "prediction":   display_prediction,
        "confidence":   round(confidence, 4),
        "model_used":   f"XGBoost + TF-IDF ({len(le_outcome.classes_)}-class, 78.9% accuracy)",
        "all_outcomes": all_outcomes,
    }

predict_case_outcome = predict_outcome