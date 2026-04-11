# One-time script to embed all processed judgments into ChromaDB
# Run from project root:
# python scripts/ingest_to_vectordb.py

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from backend.utils.embedding_utils import embed_batch
from backend.utils.text_cleaner import preprocess
from rag_pipeline.vector_store import add_documents

INPUT_PATH = BASE_DIR / "data" / "processed" / "judgments_clean.json"


def extract_text(case):
    if "full_text" in case:
        return case["full_text"]
    elif "text" in case:
        return case["text"]
    elif "content" in case:
        return case["content"]
    else:
        raise KeyError("No valid text field found in dataset.")


def clean_name(name: str) -> str:
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'[\s.…]+$', '', name).strip()
    name = re.sub(
        r'\s*(Appellant|Respondent|Petitioner|Applicant|Plaintiff|Defendant|Complainant|accused)\s*.*$',
        '', name, flags=re.IGNORECASE
    ).strip()
    return name


JUDGE_WORDS = re.compile(
    r'\b(Justice|Judge|Chief Justice|CJI|Contents)\b',
    re.IGNORECASE
)

# no\.\d removed — was incorrectly blocking clean bail_ titles containing "S/O" or "U.P."
GARBAGE_PATTERNS = re.compile(
    r'(Versus\s*\n|&\s*\n|\n\s*&|FIR\s*&|Sections\s*\d|'
    r'MBBS|NEET|CBSE|Contents\s*A\.|'
    r'^nan|^Unknown$)',
    re.IGNORECASE
)


def is_clean_title(title: str) -> bool:
    """Return True if the stored title looks like a real case name."""
    if not title or len(title.strip()) < 6:
        return False
    t = title.strip()
    if GARBAGE_PATTERNS.search(t):
        return False
    if t.count('&') > 3:
        return False
    if t.count('\n') > 1:
        return False
    if len(t) > 200:
        return False
    return True


def extract_title_from_text(full_text: str, fallback: str = "") -> str:
    if not full_text:
        return fallback if is_clean_title(fallback) else "Unknown Case"

    # Strategy 1: Multi-line block "Name .... Appellant\nVersus\nName .... Respondent"
    p1 = re.search(
        r'([A-Z][^\n]{3,120}?)\s*[.…]{2,}\s*\n?\s*'
        r'(?:Appellant|Petitioner|Applicant|Plaintiff)[^\n]*\n'
        r'[^\n]*(?:VERSUS|Versus|vs\.?)[^\n]*\n'
        r'\s*([A-Z][^\n]{3,120}?)\s*[.…]{2,}\s*\n?\s*'
        r'(?:Respondent|Defendant)',
        full_text, re.IGNORECASE,
    )
    if p1:
        a, r = clean_name(p1.group(1)), clean_name(p1.group(2))
        if 3 < len(a) < 120 and 3 < len(r) < 120:
            return f"{a} vs {r}"

    # Strategy 2: "Name\nVersus\nName" block
    p2 = re.search(
        r'\n([A-Z][^\n]{4,100})\n\s*(?:VERSUS|Versus|vs\.?)\s*\n([A-Z][^\n]{4,100})\n',
        full_text,
    )
    if p2:
        a, r = clean_name(p2.group(1)), clean_name(p2.group(2))
        if 3 < len(a) < 120 and 3 < len(r) < 120:
            return f"{a} vs {r}"

    # Strategy 3: Line-by-line ".... Appellant" scan
    lines = full_text.split('\n')
    for i, line in enumerate(lines):
        ls = line.strip()
        if re.search(r'[.…]{2,}\s*(Appellant|Petitioner|Applicant|Plaintiff)', ls, re.IGNORECASE):
            raw_a = re.sub(r'[.…]{2,}.*', '', ls).strip()
            appellant = clean_name(raw_a)
            for j in range(i + 1, min(i + 15, len(lines))):
                rl = lines[j].strip()
                if re.search(r'[.…]{2,}\s*(Respondent|Defendant)', rl, re.IGNORECASE):
                    raw_r = re.sub(r'[.…]{2,}.*', '', rl).strip()
                    respondent = clean_name(raw_r)
                    if 3 < len(appellant) < 120 and 3 < len(respondent) < 120:
                        return f"{appellant} vs {respondent}"
            break

    # Strategy 3b: Position-based inline extraction
    m_app = re.search(r'[…\.]{1,4}\s*(?:Appellant|Petitioner|Applicant|Plaintiff)', full_text, re.IGNORECASE)
    m_res = re.search(r'[…\.]{1,4}\s*(?:Respondent|Defendant)', full_text, re.IGNORECASE)

    if m_app and m_res and m_app.start() < m_res.start():
        before_app = full_text[:m_app.start()]
        after_app  = full_text[m_app.end():]

        versus_m = re.search(r'(?:VERSUS|Versus|vs\.?)\s*', after_app, re.IGNORECASE)
        if versus_m:
            after_versus = after_app[versus_m.end():]
            res_m = re.search(r'[…\.]{1,4}\s*(?:Respondent|Defendant)', after_versus, re.IGNORECASE)
            if res_m:
                respondent_raw = after_versus[:res_m.start()].strip()
                year_parts     = re.split(r'(?:OF\s+\d{4}|No\.\s*\S+\s*)\s*', before_app)
                appellant_raw  = year_parts[-1].strip() if year_parts else before_app.strip()
                a = clean_name(appellant_raw)
                r = clean_name(respondent_raw)
                if (3 < len(a) < 120 and 3 < len(r) < 120
                        and not JUDGE_WORDS.search(a)
                        and not JUDGE_WORDS.search(r)):
                    return f"{a} vs {r}"

    # Strategy 4: Inline "X versus Y" (skip judge names)
    p4 = re.search(
        r'([A-Z][A-Za-z\s&.()\-,]{4,70}?)\s+(?:VERSUS|Versus|vs\.?)\s+([A-Z][A-Za-z\s&.()\-,]{4,70})',
        full_text,
    )
    if p4:
        a, r = clean_name(p4.group(1)), clean_name(p4.group(2))
        if (3 < len(a) < 100 and 3 < len(r) < 100
                and not JUDGE_WORDS.search(a)
                and not JUDGE_WORDS.search(r)):
            return f"{a} vs {r}"

    # Fallback: use stored title if it looks clean
    if is_clean_title(fallback):
        return re.sub(r'\s+', ' ', fallback).strip()

    return "Unknown Case"


def resolve_title(case: dict) -> str:
    """
    Title resolution priority:
    1. bail_/judipl_/scraped_ cases → stored title is usually clean, use it
    2. csv_ cases → stored title is often garbage → run regex on full_text first
    3. Fallback to regex for anything else with a dirty stored title
    """
    case_id   = str(case.get("case_id", ""))
    stored    = case.get("title", "").strip()
    full_text = case.get("full_text", "")

    # bail_, judipl_, scraped_ — stored titles are clean
    if case_id.startswith(("bail_", "judipl_", "scraped_")):
        if is_clean_title(stored):
            return stored
        return extract_title_from_text(full_text, fallback=stored)

    # csv_ — stored titles are often garbage, always try regex first
    if case_id.startswith("csv_"):
        extracted = extract_title_from_text(full_text, fallback="")
        if extracted != "Unknown Case":
            return extracted
        return stored if is_clean_title(stored) else "Unknown Case"

    # anything else — try stored first, then regex
    if is_clean_title(stored):
        return stored
    return extract_title_from_text(full_text, fallback=stored)


def ingest():
    print(f"Reading dataset from: {INPUT_PATH}")

    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {INPUT_PATH}")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    print(f"Ingesting {len(cases)} cases into ChromaDB...")

    texts = [preprocess(extract_text(c)) for c in cases]
    ids   = [str(c.get("case_id", c.get("id", i))) for i, c in enumerate(cases)]

    metas = [
        {
            "title":     resolve_title(c),
            "court":     c.get("court",     "Unknown Court"),
            "year":      c.get("year",      "Unknown"),
            "case_id":   str(c.get("case_id", c.get("id", i))),
            "outcome":   str(c.get("outcome",   "") or ""),
            "case_type": str(c.get("case_type", "") or ""),
            "source":    str(c.get("source",    "") or ""),
        }
        for i, c in enumerate(cases)
    ]

    print("\n── Title extraction preview (first 8) ──")
    unknown_count = sum(1 for m in metas if m["title"] == "Unknown Case")
    for m in metas[:8]:
        print(f"  {m['title']}")
    print(f"\n  Unknown Cases: {unknown_count} / {len(metas)}")
    print("────────────────────────────────────────\n")

    batch_size = 100
    for i in range(0, len(cases), batch_size):
        batch_texts      = texts[i:i + batch_size]
        batch_ids        = ids[i:i + batch_size]
        batch_metas      = metas[i:i + batch_size]
        batch_embeddings = embed_batch(batch_texts)
        add_documents(batch_ids, batch_texts, batch_embeddings.tolist(), batch_metas)
        print(f"Ingested {min(i + batch_size, len(cases))}/{len(cases)}")

    print("\n✅ Done! Vector DB is ready with clean titles.")


if __name__ == "__main__":
    ingest()