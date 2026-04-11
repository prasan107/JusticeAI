# rag_pipeline/rag_chain.py

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import settings
from rag_pipeline.retriever import search_similar_cases

llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    temperature=0.3,
    openai_api_key=settings.OPENAI_API_KEY,
    openai_api_base=settings.OPENAI_BASE_URL,
)

SIMILARITY_THRESHOLD = 0.45

prompt_template = ChatPromptTemplate.from_template("""
You are JusticeAI — an expert Indian legal assistant with deep knowledge of:
- Indian Penal Code (IPC), CrPC, CPC, Constitutional Law, Evidence Act

INSTRUCTIONS:
- If relevant cases are provided, use them as primary evidence
- If no relevant cases, answer from your knowledge of Indian law
- Always cite specific sections and acts

=====================
{context_header}
{context}
=====================

User Question: {question}

Respond with:
1. **Legal Analysis** — explain the applicable law clearly
2. **Case Precedent** — cite relevant case from context if available
3. **Predicted Outcome** — based on law and precedents
4. **Recommended Action** — what should the person do next
""")

def get_rag_response(question: str) -> str:
    try:
        all_cases      = search_similar_cases(question)
        relevant_cases = [c for c in all_cases if c.get("similarity_score", 0) >= SIMILARITY_THRESHOLD]

        if relevant_cases:
            context_header = "Relevant Cases from Database:"
            context_text   = ""
            for c in relevant_cases:
                context_text += f"""
Case: {c['title']}
Court: {c['court']} | Year: {c.get('year', 'N/A')}
Summary: {c['summary']}
Relevance: {round(c['similarity_score'] * 100, 1)}%
-----"""
        else:
            context_header = "No directly relevant cases found."
            context_text   = "Use your general knowledge of Indian law and cite known precedents."

        messages = prompt_template.format_messages(
            context_header=context_header,
            context=context_text,
            question=question
        )
        response = llm.invoke(messages)
        return response.content

    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "429" in err:
            return "API quota temporarily exhausted. Please try again in a few minutes."
        if "Connection" in err or "timeout" in err.lower():
            return "Unable to connect to AI service. Check your connection and try again."
        return f"An error occurred: {err}"