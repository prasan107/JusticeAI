from sentence_transformers import SentenceTransformer
from backend.config import settings

# Load model once at startup
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model

def embed_text(text: str):
    model = get_model()
    return model.encode(text)

def embed_batch(texts: list):
    model = get_model()
    return model.encode(texts, show_progress_bar=True)
