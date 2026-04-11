import re
import string

def clean_text(text: str) -> str:
    """
    Full NLP preprocessing pipeline for legal text.
    Steps: lowercase → remove special chars → remove extra spaces
    """
    text = text.lower()
    text = re.sub(r"\s+", " ", text)                        # collapse whitespace
    text = re.sub(r"[^a-z0-9\s.,;:()\'\-]", "", text)   # keep useful punctuation
    text = text.strip()
    return text

def tokenize(text: str):
    return text.split()

def preprocess(text: str) -> str:
    return clean_text(text)
