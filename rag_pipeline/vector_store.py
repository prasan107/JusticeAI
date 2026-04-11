# ChromaDB vector store setup

import chromadb
from pathlib import Path
from backend.config import settings

# 🔥 Always resolve absolute project root
BASE_DIR = Path(__file__).resolve().parent.parent

PERSIST_PATH = str(BASE_DIR / settings.CHROMA_DB_PATH)

print(f"Using ChromaDB path: {PERSIST_PATH}")

# Create persistent client
client = chromadb.PersistentClient(path=PERSIST_PATH)

# Create or load collection
collection = client.get_or_create_collection(name="legal_cases")


def add_documents(ids, texts, embeddings, metadatas):
    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )


def query_collection(query_embedding, top_k=5):
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    return results
