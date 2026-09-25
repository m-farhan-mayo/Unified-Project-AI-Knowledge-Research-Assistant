import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing.")

    return psycopg.connect(database_url)


def insert_document_chunk(chunk_text: str, embedding: list[float]):
    connection = get_connection()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO document_chunks (chunk_text, embedding)
                VALUES (%s, %s)
                """,
                (chunk_text, embedding),
            )

    connection.close()


def get_document_chunks():
    connection = get_connection()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, chunk_text
                FROM document_chunks
                """
            )

            rows = cursor.fetchall()

    connection.close()

    return rows


def search_similar_chunks(query_embedding: list[float], limit: int = 3):
    connection = get_connection()

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    chunk_text,
                    embedding <=> %s::vector AS distance
                FROM document_chunks
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (query_embedding, query_embedding, limit),
            )

            rows = cursor.fetchall()

    connection.close()

    return rows

def insert_document_chunks(chunks: list[str], embeddings: list[list[float]]):
    connection = get_connection()

    with connection:
        with connection.cursor() as cursor:
            for chunk, embedding in zip(chunks, embeddings):
                cursor.execute(
                    """
                    INSERT INTO document_chunks (chunk_text, embedding)
                    VALUES (%s, %s)
                    """,
                    (chunk, embedding),
                )

    connection.close()