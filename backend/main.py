import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import RateLimitError
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
    insert_document_chunk,
    insert_document_chunks,
    get_document_chunks,
    search_similar_chunks,
)
from app.services.llm_service import ask_llm, ask_llm_with_tools
from app.services.tools import search_web, send_email
from app.services.pdf_service import (
    extract_text_from_pdf,
    chunk_text,
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

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="The current user message.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous user and assistant messages in chronological order.",
    )


class ChatResult(BaseModel):
    answer: str = Field(description="The assistant's final response.")
    sources: list[Any] = Field(
        description="Web or research sources used to produce the answer."
    )
    email_status: dict[str, Any] = Field(
        description="Structured status of emailing the assistant's answer to the configured recipient."
    )


class ChatApiResponse(BaseModel):
    response: ChatResult


class PdfUploadResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks: list[str]


@app.post(
    "/api/chat",
    response_model=ChatApiResponse,
    tags=["chat"],
    summary="Send a chat message",
    description=(
        "Sends the current message and optional conversation history to the "
        "assistant, then emails the answer to CHAT_EMAIL_TO or SMTP_USERNAME. "
        "The response contains the answer, research sources, and email status."
    ),
)
def chat(request: ChatRequest):
    response = ask_llm_with_tools(
        request.message,
        [message.model_dump() for message in request.history],
    )
    recipient = os.getenv("CHAT_EMAIL_TO") or os.getenv("SMTP_USERNAME")
    if recipient:
        email_status = send_email(
            to=recipient,
            subject="AI Assistant response",
            body=response["answer"],
        )
    else:
        email_status = {
            "success": False,
            "tool": "send_email",
            "message": "Email was not sent: configure CHAT_EMAIL_TO or SMTP_USERNAME.",
        }

    response["email_status"] = email_status

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
    summary="Upload and extract a PDF",
    description="Extracts PDF text and returns it as overlapping chunks.",
    responses={400: {"description": "The uploaded file is not a PDF."}},
)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename:
        return {"error": "No file provided."}

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(contents)
        temp_file_path = temp_file.name

    try:
        text = extract_text_from_pdf(temp_file_path)
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
    finally:
        os.unlink(temp_file_path)

    return {
        "filename": file.filename,
        "total_chunks": len(chunks),
        "chunks": chunks
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

    insert_document_chunk(text, vector)

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
    text = extract_text_from_pdf(pdf_path)

    chunks = chunk_text(
        text,
        chunk_size=1000,
        overlap=200
    )

    return {
        "total_chunks": len(chunks),
        "first_chunk": chunks[0],
        "second_chunk": chunks[1]
    }


@app.get("/api/chunk-embedding-test")
def chunk_embedding_test():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pdf_path = os.path.join(project_root, "research.pdf")
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
        "embedding_dimensions": len(embeddings[0])
    }


@app.get("/api/store-pdf-test")
def store_pdf_test():
    text = extract_text_from_pdf("/home/dev/Desktop/Unified Project — AI Knowledge & Research Assistant/research.pdf")

    chunks = chunk_text(
        text,
        chunk_size=1000,
        overlap=200
    )

    embeddings = get_embeddings_for_chunks(chunks)

    insert_document_chunks(chunks, embeddings)

    return {
        "message": "PDF chunks and embeddings stored successfully.",
        "total_chunks": len(chunks),
        "total_embeddings": len(embeddings)
    }


@app.get("/api/rag-test")
def rag_test():
    question = "What cloud platforms does Farhan have experience with?"

    result = answer_with_rag(question)

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