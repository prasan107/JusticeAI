# backend/api/ocr.py

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.ocr_service import extract_text_from_file
from rag_pipeline.retriever import search_similar_cases
from rag_pipeline.rag_chain import get_rag_response
import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)
from ml_pipeline.predictor import predict_outcome


router = APIRouter()

@router.post("/analyse")
async def analyse_document(file: UploadFile = File(...)):
    """
    Full pipeline for uploaded legal document:
    1. OCR  → extract text
    2. Search → find similar cases
    3. Predict → outcome probability
    4. LLM → AI explanation
    """
    # Validate file type
    allowed = ["pdf", "png", "jpg", "jpeg", "tiff", "bmp"]
    ext = file.filename.lower().split(".")[-1]
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    # Step 1 — OCR
    try:
        file_bytes = await file.read()
        extracted_text = extract_text_from_file(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

    if not extracted_text or len(extracted_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="Could not extract readable text from the file.")

    # Use first 600 chars for analysis (most relevant part)
    analysis_text = extracted_text[:600]

    # Step 2 — Search similar cases
    try:
        similar_cases = search_similar_cases(analysis_text)
    except Exception:
        similar_cases = []

    # Step 3 — Predict outcome
    try:
        prediction = predict_outcome(
            case_type   = "Criminal",
            court       = "High Court",
            year        = 2021,
            description = analysis_text
        )
    except Exception:
        prediction = {"prediction": "Unknown", "confidence": 0.0, "model_used": "N/A", "all_outcomes": {}}

    # Step 4 — LLM reasoning
    try:
        ai_explanation = get_rag_response(
            f"Analyse this legal document and provide legal insights:\n\n{analysis_text}"
        )
    except Exception as e:
        ai_explanation = f"AI analysis unavailable: {str(e)}"

    return {
        "filename":       file.filename,
        "word_count":     len(extracted_text.split()),
        "extracted_text": extracted_text[:1000],
        "similar_cases":  similar_cases,
        "prediction":     prediction,
        "ai_explanation": ai_explanation,
    }


@router.post("/extract")
async def extract_only(file: UploadFile = File(...)):
    """Just extract text from file — no analysis."""
    try:
        file_bytes = await file.read()
        text = extract_text_from_file(file_bytes, file.filename)
        return {
            "filename":   file.filename,
            "text":       text,
            "word_count": len(text.split())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))