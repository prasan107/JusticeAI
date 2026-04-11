# backend/api/legal.py
# ONE smart endpoint that does everything:
# OCR (optional) → Search → Predict → Explain

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
import sys, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from rag_pipeline.retriever import search_similar_cases
from rag_pipeline.rag_chain import get_rag_response
from ml_pipeline.predictor import predict_outcome

router = APIRouter()

SIMILARITY_THRESHOLD = 0.45  # below this → cases not relevant → LLM uses general knowledge

def _filter_relevant_cases(cases: list) -> list:
    """Keep only cases with meaningful similarity score."""
    return [c for c in cases if c.get("similarity_score", 0) >= SIMILARITY_THRESHOLD]

def _run_full_pipeline(text: str, case_type: str, court: str, year: int) -> dict:
    """Core pipeline: Search → Predict → Explain."""

    # Step 1 — Search
    all_cases = search_similar_cases(text[:600])
    relevant_cases = _filter_relevant_cases(all_cases)
    fallback_used = len(relevant_cases) == 0

    # Step 2 — Predict
    try:
        prediction = predict_outcome(
            case_type   = case_type,
            court       = court,
            year        = year,
            description = text[:600]
        )
    except Exception as e:
        prediction = {
            "prediction":  "Unknown",
            "confidence":  0.0,
            "model_used":  "N/A",
            "all_outcomes": {}
        }

    # Step 3 — Explain (use relevant cases if available, else fallback to LLM knowledge)
    try:
        ai_explanation = get_rag_response(text[:800])
    except Exception as e:
        ai_explanation = f"AI analysis unavailable: {str(e)}"

    return {
        "similar_cases":   relevant_cases,
        "total_retrieved": len(all_cases),
        "fallback_used":   fallback_used,
        "prediction":      prediction,
        "ai_explanation":  ai_explanation,
    }


# ── Endpoint 1: Text input ─────────────────────────────────────
class TextAnalyzeRequest(BaseModel):
    query:     str
    case_type: Optional[str] = "Criminal"
    court:     Optional[str] = "High Court"
    year:      Optional[int] = 2021

@router.post("/analyze")
def analyze_text(req: TextAnalyzeRequest):
    """Analyze a legal query — Search + Predict + Explain."""
    result = _run_full_pipeline(req.query, req.case_type, req.court, req.year)
    return {
        "input_type": "text",
        "query":       req.query[:300],
        **result
    }


# ── Endpoint 2: File input (OCR + pipeline) ────────────────────
@router.post("/analyze-document")
async def analyze_document(
    file:      UploadFile = File(...),
    case_type: str        = Form("Criminal"),
    court:     str        = Form("High Court"),
    year:      int        = Form(2021),
):
    """Upload PDF or image → OCR → Search → Predict → Explain."""
    from services.ocr_service import extract_text_from_file

    # OCR
    try:
        file_bytes     = await file.read()
        extracted_text = extract_text_from_file(file_bytes, file.filename)
    except Exception as e:
        return {"error": f"OCR failed: {str(e)}"}

    if not extracted_text or len(extracted_text.strip()) < 20:
        return {"error": "Could not extract readable text from file."}

    result = _run_full_pipeline(extracted_text, case_type, court, year)

    return {
        "input_type":     "document",
        "filename":       file.filename,
        "word_count":     len(extracted_text.split()),
        "extracted_text": extracted_text[:1000],
        **result
    }