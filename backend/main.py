import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import search, predict, chatbot, ocr
from api import legal

app = FastAPI(title="JusticeAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(predict.router, prefix="/predict", tags=["Predict"])
app.include_router(chatbot.router, prefix="/chat", tags=["Chatbot"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(legal.router, prefix="/legal", tags=["Legal"])

@app.get("/")
def health_check():
    return {"status": "JusticeAI backend is running ✅"}