from app.services.embedding_service import get_embedding
from app.services.database import search_similar_chunks
from app.services.llm_service import ask_llm


def answer_with_rag(
    question: str,
    document_id: int,
    history: list[dict] | None = None,
) -> dict:
    query_embedding = get_embedding(question)

    rows = search_similar_chunks(
        query_embedding=query_embedding,
        document_id=document_id,
        limit=5,
    )

    if not rows:
        return {
            "answer": (
                "I couldn't find relevant information "
                "in the selected document."
            ),
            "sources": [],
            "email_status": None,
        }

    sources = []

    context_sections = []

    for row in rows:
        (
            chunk_id,
            chunk_text,
            page_number,
            chunk_index,
            row_document_id,
            filename,
            distance,
        ) = row

        source = {
            "type": "document",
            "document_id": row_document_id,
            "filename": filename,
            "title": filename,
            "page_number": page_number,
            "chunk_index": chunk_index,
            "chunk_id": chunk_id,
            "distance": float(distance),
        }

        sources.append(source)

        context_sections.append(
            f"""
SOURCE:
File: {filename}
Page: {page_number}
Chunk: {chunk_index}

CONTENT:
{chunk_text}
""".strip()
        )

    context = "\n\n---\n\n".join(
        context_sections
    )

    messages = [
        {
            "role": "system",
            "content": """
You are an AI Knowledge Assistant.

The user is asking a question about an uploaded document.

Use the provided document context as the primary source.

Rules:

1. Do not invent information from the document.
2. If the requested information is not supported by the provided context,
   clearly say that the document does not provide enough information.
3. Answer clearly and concisely.
4. When using document information, mention the relevant page when useful.
5. Do not invent page numbers or citations.
""",
        }
    ]

    # Preserve a small amount of conversation context.
    if history:
        messages.extend(history[-6:])

    messages.append(
        {
            "role": "user",
            "content": f"""
DOCUMENT CONTEXT:

{context}


QUESTION:

{question}
""",
        }
    )

    answer = ask_llm(messages)

    return {
        "answer": answer,
        "sources": sources,
        "email_status": None,
    }