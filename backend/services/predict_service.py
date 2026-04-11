# backend/services/predict_service.py
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from ml_pipeline.predictor import predict_outcome  # fixed function name
from schemas.schemas import PredictRequest, PredictResponse

def run_prediction(request: PredictRequest) -> PredictResponse:
    description = getattr(request, 'query', '') or ''
    result = predict_outcome(
        case_type=request.case_type,
        court=request.court,
        year=request.year,
        description=description,
    )
    return PredictResponse(
        prediction=result["prediction"],
        confidence=result["confidence"],
        model_used=result["model_used"],
        all_outcomes=result.get("all_outcomes", {}),
    )