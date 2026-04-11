# backend/api/chatbot.py

from fastapi import APIRouter
from backend.schemas.schemas import ChatRequest, ChatResponse
from backend.services.chatbot_service import run_chat

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/ask", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = run_chat(request.message)
    return ChatResponse(reply=result["reply"])
