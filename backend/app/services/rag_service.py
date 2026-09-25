from app.services.embedding_service import get_embedding
from app.services.database import search_similar_chunks
from app.services.llm_service import ask_llm

def answer_with_rag(
    question: str,
) -> dict[str, object]:
    query_embedding = get_embedding(question)

    results = search_similar_chunks(
        query_embedding,
        limit=3
    )

    sources = [
        {
            "chunk_id": row[0],
            "text": row[1],
            "distance": row[2]
        }
        for row in results
    ]

    if not sources:
        return {
            "answer": "I don't have enough information to answer that.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(
        source["text"]
        for source in sources
    )

    prompt = f"""
Answer the question using only the context below.

If the answer is not available in the context, say:
"I don't have enough information to answer that."

Context:
{context}

Question:
{question}

Answer:
"""

    answer = ask_llm(prompt)

    return {
    "answer": answer,
    "sources": [
        f"Document Chunk {source['chunk_id']}"
        for source in sources
    ]
}