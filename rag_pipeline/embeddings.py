# Generates and stores embeddings for legal judgments
from backend.utils.embedding_utils import embed_batch
from backend.utils.text_cleaner import preprocess

def generate_embeddings(texts: list):
    cleaned = [preprocess(t) for t in texts]
    embeddings = embed_batch(cleaned)
    return embeddings
