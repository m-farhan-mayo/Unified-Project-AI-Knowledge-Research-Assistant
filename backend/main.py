import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.genai.errors import APIError as GoogleAPIError
from openai import RateLimitError, APIConnectionError, APIStatusError, APITimeoutError
from pydantic import BaseModel, Field
from typing import Any
import tempfile
from app.services.embedding_service import (
    get_embeddings_for_chunks,
)
from app.services.rag_service import answer_with_rag
from app.services.database import (
    create_document,
    insert_document_chunks,
)
from app.services.llm_service import ask_llm_with_tools
from app.services.pdf_service import (
    extract_pages_from_pdf,
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
        "and upload PDFs for indexing. Chat requests use a session ID "
        "to retrieve conversation history and return answers with sources."
    ),
    version="1.0.0",
    openapi_tags=[
        {"name": "chat", "description": "Conversation and AI-assisted research."},
        {"name": "documents", "description": "PDF upload and text extraction."},
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


@app.exception_handler(GoogleAPIError)
async def handle_embedding_api_error(request: Request, exc: GoogleAPIError):
    if exc.code == 429:
        return JSONResponse(
            status_code=429,
            content={"detail": (
                "Google's embedding API quota or rate limit has been reached. "
                "PDF indexing and document questions are temporarily unavailable. "
                "Check your Gemini embedding quota and billing, then retry once capacity is available."
            )},
        )
    if exc.code >= 500:
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": "30"},
            content={"detail": "Google's embedding service is temporarily unavailable. Please try again shortly."},
        )
    return JSONResponse(
        status_code=502,
        content={"detail": "Google rejected the embedding request. Check the backend API key and embedding model access."},
    )


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

@app.get("/api/health", tags=["system"], summary="Check API liveness")
def health():
    """Confirm the API is serving requests without calling external services."""
    return {"status": "ok"}
