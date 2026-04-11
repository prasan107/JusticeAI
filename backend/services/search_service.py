# Module 1 — Semantic Search Service
# rag_pipeline is found via sys.path set in main.py

from rag_pipeline.retriever import search_similar_cases

def run_search(query: str):
    """
    Takes a user query string.
    Returns list of similar legal cases.
    """
    results = search_similar_cases(query)
    return results