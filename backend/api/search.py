from fastapi import APIRouter
from schemas.schemas import SearchRequest, SearchResponse
from services.search_service import run_search

router = APIRouter()

@router.post("/query", response_model=SearchResponse)
def search_cases(request: SearchRequest):
    results = run_search(request.query)
    return SearchResponse(results=results)
