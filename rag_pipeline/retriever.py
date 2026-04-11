import re
from backend.utils.embedding_utils import embed_text
from backend.utils.text_cleaner import preprocess
from rag_pipeline.vector_store import query_collection


def parse_ipc_and_outcome(full_text: str):
    ipc_sections = []
    outcome = ""

    # IPC sections — stop before 'crime:'
    ipc_match = re.search(r"ipc:\s*(.*?)(?:\s+crime:|\s*$)", full_text, re.IGNORECASE)
    if ipc_match:
        raw = ipc_match.group(1)
        ipc_sections = re.findall(r"[a-zA-Z0-9]+", raw)
        ipc_sections = [s for s in ipc_sections if s.lower()
                        not in ("ipc", "crime", "section", "and", "or")]

    # Only check the last 400 chars for outcome
    # Summary sentence is always at the end — avoids false matches mid-text
    summary_text = full_text[-400:].lower()

    # ── Bail Rejected ─────────────────────────────────────────────────────
    bail_rejected = (
        "set aside bail" in summary_text
        or "cancelled bail" in summary_text
        or "cancelled anticipatory bail" in summary_text
        or "bail was cancelled" in summary_text
        or "cancelling the bail" in summary_text
        or "bail rejected" in summary_text
        or "rejected bail" in summary_text
        or "bail was rejected" in summary_text
        or "denied bail" in summary_text
        or "bail was denied" in summary_text
        or "bail denied" in summary_text
        or "refused bail" in summary_text
        or "rejected regular bail" in summary_text
        or "rejected anticipatory bail" in summary_text
        or "bail application was rejected" in summary_text
        or "bail application rejected" in summary_text
        # ✅ Regex: catches "rejected the third/second/first/a bail application"
        or bool(re.search(
            r"rejected\s+(?:the\s+)?(?:third|second|first|this|a\s+)?bail\s+application",
            summary_text
        ))
    )

    # ── Bail Granted ──────────────────────────────────────────────────────
    bail_granted = (
        "refused to cancel bail" in summary_text
        or "cancellation was unwarranted" in summary_text
        or "bail was granted" in summary_text
        or "granted bail" in summary_text
        or "granted regular bail" in summary_text
        or "granted anticipatory bail" in summary_text
        or "confirmed bail" in summary_text
        or "bail confirmed" in summary_text
    )

    # ── Assign outcome — rejection takes priority over granted ────────────
    if bail_rejected:
        outcome = "Bail Rejected"
    elif bail_granted:
        outcome = "Bail Granted"
    elif "appeal dismissed" in summary_text or "dismissed the appeal" in summary_text:
        outcome = "Appeal Dismissed"
    elif "appeal allowed" in summary_text or "allowed the appeal" in summary_text:
        outcome = "Appeal Allowed"
    elif "acquitted" in summary_text:
        outcome = "Acquitted"
    elif "convicted" in summary_text:
        outcome = "Convicted"

    return ipc_sections, outcome


def search_similar_cases(query: str, top_k: int = 5):

    # 1 — Clean query
    cleaned_query = preprocess(query)

    # 2 — Create embedding
    query_embedding = embed_text(cleaned_query)

    # 3 — Query vector DB
    results = query_collection(query_embedding, top_k=top_k)

    cases = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for i, doc in enumerate(documents):
        meta = metadatas[i]

        # Parse IPC sections + outcome from full_text
        ipc_sections, parsed_outcome = parse_ipc_and_outcome(doc)

        # Use stored outcome if available, fall back to parsed
        stored_outcome = meta.get("outcome", "") or ""
        final_outcome  = stored_outcome if stored_outcome else parsed_outcome

        # Safely convert year
        raw_year   = meta.get("year")
        year_value = raw_year if isinstance(raw_year, int) else None

        cases.append({
            "case_id":          meta.get("case_id", ""),
            "title":            meta.get("title", ""),
            "court":            meta.get("court", ""),
            "year":             year_value,
            "case_type":        meta.get("case_type", ""),
            "outcome":          final_outcome,
            "source":           meta.get("source", ""),
            "summary":          doc[:500],
            "full_text":        doc,
            "ipc_sections":     ipc_sections,
            "similarity_score": round(float(1 - distances[i] / 2), 4)
        })

    return cases