# backend/api/predict.py
# POST /predict/outcome endpoint

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict

router = APIRouter()

class PredictRequest(BaseModel):
    case_type:   str                        # "Criminal", "Civil", "Family"
    court:       str                        # "Supreme Court of India", "High Court"
    year:        int                        # 2020
    description: Optional[str] = ""        # free text description of the case

class PredictResponse(BaseModel):
    prediction:  str
    confidence:  float
    model_used:  str
    all_outcomes: Dict[str, float]

@router.post("/outcome", response_model=PredictResponse)
def predict_outcome(req: PredictRequest):
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from ml_pipeline.predictor import predict_outcome as run_predict

    result = run_predict(
        case_type   = req.case_type,
        court       = req.court,
        year        = req.year,
        description = req.description or "",
    )
    return PredictResponse(**result)