import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import RateLimitError, APIConnectionError, APIStatusError, APITimeoutError
from pydantic import BaseModel, Field
from typing import Any, Literal
import tempfile
from app.services.embedding_service import (
    get_embedding,
    get_embeddings_for_chunks,
)
from app.services.rag_service import answer_with_rag
from app.services.database import (
    get_connection,
    create_document,
    insert_document_chunks,
    get_document_chunks,
    search_similar_chunks,
)
from app.services.llm_service import ask_llm, ask_llm_with_tools
from app.services.tools import search_web, send_email
from app.services.pdf_service import (
    extract_text_from_pdf,
    extract_pages_from_pdf,
    chunk_text,
    chunk_pdf_pages,
)
from app.services.redis_service import (
    load_history,
    save_history,
)





load_dotenv()


app = FastAPI(
    title="Unified Project - AI Knowledge & Research Assistant",
    description=(
        "Chat with an AI assistant, research topics with cited web sources, "
        "and upload PDFs for text extraction. Chat requests accept prior "
        "user/assistant messages and return an answer with source data."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "chat", "description": "Conversation and AI-assisted research."},
        {"name": "documents", "description": "PDF upload and text extraction."},
        {"name": "data", "description": "Embeddings, PostgreSQL, and vector search."},
        {"name": "system", "description": "Service status and configuration checks."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitError)
async def handle_rate_limit_error(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "The Gemini API quota or rate limit has been reached. Check your Gemini API quota and retry later."
        },
    )

@app.exception_handler(APIConnectionError)
async def handle_ai_connection_error(request: Request, exc: APIConnectionError):
    return JSONResponse(
        status_code=504 if isinstance(exc, APITimeoutError) else 503,
        headers={"Retry-After": "30"},
        content={"detail": "Gemini is temporarily unreachable or timed out. Please try again shortly."},
    )


@app.exception_handler(APIStatusError)
async def handle_ai_status_error(request: Request, exc: APIStatusError):
    if exc.status_code >= 500:
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": "30"},
            content={"detail": "Gemini is temporarily unavailable due to high demand. Please try again shortly."},
        )
    return JSONResponse(
        status_code=502,
        content={"detail": "Gemini rejected the request. Check the backend API key, configured model, and provider access."},
    )


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        description="Unique identifier for the conversation session.",
    )

    message: str = Field(
        min_length=1,
        description="The current user message.",
    )

    document_id: int | None = Field(
        default=None,
        description=(
            "Optional uploaded document ID. "
            "When provided, the assistant answers using RAG."
        ),
    )


class ChatResult(BaseModel):
    answer: str = Field(
        description="The assistant's final response."
    )

    sources: list[Any] = Field(
        default_factory=list,
        description="Sources used to produce the answer."
    )

    email_status: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Email tool result when the user explicitly requests email."
        ),
    )


class ChatApiResponse(BaseModel):
    response: ChatResult


class PdfUploadResponse(BaseModel):
    document_id: int
    filename: str
    total_pages: int
    total_chunks: int
    message: str


@app.post(
    "/api/chat",
    response_model=ChatApiResponse,
    tags=["chat"],
    summary="Send a chat message",
    description=(
        "Answers using normal AI/tool calling, or uses RAG "
        "when document_id is provided."
    ),
)
def chat(request: ChatRequest):
    history = load_history(
        request.session_id
    ) or []

    # --------------------------------------------------
    # DOCUMENT CHAT / RAG
    # --------------------------------------------------

    if request.document_id is not None:
        response = answer_with_rag(
            question=request.message,
            document_id=request.document_id,
            history=history,
        )

    # --------------------------------------------------
    # NORMAL AI + TOOLS
    # --------------------------------------------------

    else:
        response = ask_llm_with_tools(
            request.message,
            history,
        )

    updated_history = history + [
        {
            "role": "user",
            "content": request.message,
        },
        {
            "role": "assistant",
            "content": response["answer"],
        },
    ]

    save_history(
        request.session_id,
        updated_history,
    )

    return {
        "response": response
    }

@app.get("/")
def home():
    return {
        "message": "AI Knowledge & Research Assistant API is running"
    }

@app.post(
    "/api/upload-pdf",
    response_model=PdfUploadResponse,
    tags=["documents"],
    summary="Upload and index a PDF",
    description=(
        "Extracts text from a PDF, creates chunks, "
        "generates embeddings and stores them in pgvector."
    ),
)
def upload_pdf(
    file: UploadFile = File(...),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided.",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    contents = file.file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
    ) as temp_file:
        temp_file.write(contents)
        temp_file_path = temp_file.name

    try:
        try:
            pages = extract_pages_from_pdf(temp_file_path)
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail="The file is not a readable PDF.") from exc

        if not pages:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text was found in the PDF."
                ),
            )

        chunks = chunk_pdf_pages(
            pages,
            chunk_size=1000,
            overlap=200,
        )

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text chunks could be created.",
            )

        # Extract only text for the embedding model.
        chunk_texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = get_embeddings_for_chunks(
            chunk_texts
        )

        document_id = create_document(
            filename=file.filename,
            content_type=file.content_type,
            total_pages=len(pages),
            total_chunks=len(chunks),
        )

        insert_document_chunks(
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
        )

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "total_pages": len(pages),
        "total_chunks": len(chunks),
        "message": (
            "PDF uploaded and indexed successfully."
        ),
    }

@app.get("/api/test")
def test_api():
    return {
        "message": "Hello from FastAPI"
    }


@app.get("/api/config-test")
def config_test():
    return {
        "app_name": os.getenv("APP_NAME"),
        "environment": os.getenv("ENVIRONMENT")
    }


@app.get("/api/llm-test")
def llm_test():
    response = ask_llm("Explain what a data pipeline is in one sentence.")
    return {
        "response": response
    }



@app.get("/api/embedding-test")
def embedding_test():
    vector = get_embedding(
        "Airflow is used to orchestrate data pipelines."
    )

    return {
        "dimensions": len(vector),
        "first_values": vector[:5]
    }

@app.get("/api/db-test")
def db_test():
    connection = get_connection()

    connection.close()

    return {
        "message": "PostgreSQL connection successful."
    }


@app.get("/api/vector-insert-test")
def vector_insert_test():
    text = "Airflow is used to orchestrate data pipelines."

    vector = get_embedding(text)

    document_id = create_document("Diagnostic sample", "text/plain", 1, 1)
    insert_document_chunks(document_id, [{"text": text, "page_number": 1, "chunk_index": 0}], [vector])

    return {
        "message": "Embedding inserted successfully."
    }


@app.get("/api/chunks-test")
def chunks_test():
    chunks = get_document_chunks()

    return {
        "chunks": chunks
    }

@app.get("/api/vector-search-test")
def vector_search_test():
    question = "What cloud platforms does Farhan have experience with?"

    query_embedding = get_embedding(question)

    results = search_similar_chunks(
        query_embedding,
        limit=3
    )

    return {
        "question": question,
        "results": results
    }

@app.get("/api/chunk-test")
def chunk_test():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pdf_path = os.path.join(project_root, "research.pdf")
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="Sample PDF is not installed. Use /api/upload-pdf instead.")
    text = extract_text_from_pdf(pdf_path)

    chunks = chunk_text(
        text,
        chunk_size=1000,
        overlap=200
    )

    return {
        "total_chunks": len(chunks),
        "first_chunk": chunks[0] if chunks else None,
        "second_chunk": chunks[1] if len(chunks) > 1 else None
    }


@app.get("/api/chunk-embedding-test")
def chunk_embedding_test():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pdf_path = os.path.join(project_root, "research.pdf")
    if not os.path.isfile(pdf_path):
        raise HTTPException(status_code=404, detail="Sample PDF is not installed. Use /api/upload-pdf instead.")
    text = extract_text_from_pdf(pdf_path)

    chunks = chunk_text(
        text,
        chunk_size=1000,
        overlap=200
    )

    embeddings = get_embeddings_for_chunks(chunks)

    return {
        "total_chunks": len(chunks),
        "total_embeddings": len(embeddings),
        "embedding_dimensions": len(embeddings[0]) if embeddings else 0
    }




@app.get("/api/rag-test")
def rag_test(document_id: int = Query(..., gt=0)):
    question = "What cloud platforms does Farhan have experience with?"

    result = answer_with_rag(question, document_id=document_id)

    return {
        "question": question,
        **result
    }


@app.get("/api/history-test")
def history_test():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "What is Apache Airflow?"
        },
        {
            "role": "assistant",
            "content": "Apache Airflow is a workflow orchestration platform used to schedule and manage data workflows."
        },
        {
            "role": "user",
            "content": "What is it mainly used for?"
        }
    ]

    answer = ask_llm(messages)

    return {
        "answer": answer
    }


@app.get("/api/tool-test")
def tool_test():
    response = ask_llm_with_tools(
        "Research Apache Kafka and give me a structured report."
    )

    return {
        "response": response
    }

@app.get("/api/search-test")
def search_test():
    return search_web(
        "Latest Databricks news"
    )



from app.services.research_service import research_topic

@app.get("/api/research-test")
def research_test():
    result = research_topic("Apache Kafka")

    return result