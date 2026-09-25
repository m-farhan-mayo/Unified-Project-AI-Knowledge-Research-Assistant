import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import RateLimitError
from pydantic import BaseModel
import tempfile
from app.services.pdf_service import extract_text_from_pdf
from app.services.pdf_service import extract_text_from_pdf, chunk_text
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


load_dotenv()

from app.services.llm_service import ask_llm, ask_llm_with_tools, execute_tool

app = FastAPI()

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

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

@app.post("/api/chat")
def chat(request: ChatRequest):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        }
    ]

    messages.extend(request.history)

    messages.append(
        {
            "role": "user",
            "content": request.message
        }
    )

    response = ask_llm(messages)

    return {
        "response": response
    }

@app.get("/")
def home():
    return {
        "message": "AI Knowledge & Research Assistant API is running"
    }

@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename:
        return {"error": "No file provided."}

    if file.content_type != "application/pdf":
        return {"error": "Only PDF files are allowed."}

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(contents)
        temp_file_path = temp_file.name

    text = extract_text_from_pdf(temp_file_path)

    chunks = chunk_text(
        text,
        chunk_size=1000,
        overlap=200
    )

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
        "What is Farhan's name?"
    )

    return {
        "response": response
    }