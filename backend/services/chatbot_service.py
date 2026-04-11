# Module 3 — Legal Chatbot Service
# rag_pipeline is found via sys.path set in main.py

# backend/services/chatbot_service.py

from rag_pipeline.rag_chain import get_rag_response

def run_chat(message: str):
    """
    Takes user message.
    Returns AI-generated legal explanation.
    """
    response = get_rag_response(message)
    return {"reply": response}
