from pydantic import BaseModel
from typing import List, Optional

# ---------- Module 1: Search ----------
class SearchRequest(BaseModel):
    query: str

class CaseResult(BaseModel):
    case_id:          str
    title:            str
    court:            str
    year:             Optional[int]
    case_type:        Optional[str] = ""
    outcome:          Optional[str] = ""
    source:           Optional[str] = ""
    summary:          str           # short preview (500 chars)
    full_text:        Optional[str] = ""   # ← full judgment text for modal
    ipc_sections:     Optional[list] = []
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[CaseResult]

# ---------- Module 2: Predict ----------
class PredictRequest(BaseModel):
    case_type:   str
    court:       str
    year:        int
    description: Optional[str] = ""
    ipc_sections:  Optional[List[str]] = []
    accused_count: Optional[int] = 1

class PredictResponse(BaseModel):
    prediction:   str
    confidence:   float
    model_used:   str
    all_outcomes: Optional[dict] = {}

# ---------- Module 3: Chatbot ----------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# ---------- Module 4: OCR ----------
class OCRResponse(BaseModel):
    filename:       str
    extracted_text: str
    word_count:     int