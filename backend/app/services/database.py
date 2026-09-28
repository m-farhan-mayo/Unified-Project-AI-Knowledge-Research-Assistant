import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing.")

    return psycopg.connect(database_url)


def create_document(
    filename: str,
    content_type: str | None,
    total_pages: int,
    total_chunks: int,
) -> int:
    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO documents (
                        filename,
                        content_type,
                        total_pages,
                        total_chunks
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        filename,
                        content_type,
                        total_pages,
                        total_chunks,
                    ),
                )

                row = cursor.fetchone()

                if row is None:
                    raise RuntimeError(
                        "Failed to create document record."
                    )

                return row[0]

    finally:
        connection.close()


def insert_document_chunks(
    document_id: int,
    chunks: list[dict],
    embeddings: list[list[float]],
):
    if len(chunks) != len(embeddings):
        raise ValueError(
            "The number of chunks and embeddings must match."
        )

    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                for chunk, embedding in zip(
                    chunks,
                    embeddings,
                ):
                    cursor.execute(
                        """
                        INSERT INTO document_chunks (
                            document_id,
                            page_number,
                            chunk_index,
                            chunk_text,
                            embedding
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            document_id,
                            chunk["page_number"],
                            chunk["chunk_index"],
                            chunk["text"],
                            embedding,
                        ),
                    )

    finally:
        connection.close()


def search_similar_chunks(
    query_embedding: list[float],
    document_id: int | None = None,
    limit: int = 5,
):
    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:

                if document_id is not None:
                    cursor.execute(
                        """
                        SELECT
                            dc.id,
                            dc.chunk_text,
                            dc.page_number,
                            dc.chunk_index,
                            dc.document_id,
                            d.filename,
                            dc.embedding <=> %s::vector AS distance
                        FROM document_chunks dc
                        JOIN documents d
                            ON d.id = dc.document_id
                        WHERE dc.document_id = %s
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (
                            query_embedding,
                            document_id,
                            query_embedding,
                            limit,
                        ),
                    )

                else:
                    cursor.execute(
                        """
                        SELECT
                            dc.id,
                            dc.chunk_text,
                            dc.page_number,
                            dc.chunk_index,
                            dc.document_id,
                            d.filename,
                            dc.embedding <=> %s::vector AS distance
                        FROM document_chunks dc
                        JOIN documents d
                            ON d.id = dc.document_id
                        ORDER BY dc.embedding <=> %s::vector
                        LIMIT %s
                        """,
                        (
                            query_embedding,
                            query_embedding,
                            limit,
                        ),
                    )

                return cursor.fetchall()

    finally:
        connection.close()


def get_document(document_id: int):
    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        filename,
                        content_type,
                        total_pages,
                        total_chunks,
                        created_at
                    FROM documents
                    WHERE id = %s
                    """,
                    (document_id,),
                )

                return cursor.fetchone()

    finally:
        connection.close()


def get_documents():
    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        filename,
                        content_type,
                        total_pages,
                        total_chunks,
                        created_at
                    FROM documents
                    ORDER BY created_at DESC
                    """
                )

                return cursor.fetchall()

    finally:
        connection.close()


# ------------------------------------------------------------------
# Legacy helpers kept temporarily because your existing /test routes
# reference them.
# ------------------------------------------------------------------

def insert_document_chunk(
    chunk_text: str,
    embedding: list[float],
):
    raise RuntimeError(
        "insert_document_chunk() is deprecated. "
        "Use create_document() and insert_document_chunks()."
    )


def get_document_chunks():
    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        dc.id,
                        dc.document_id,
                        d.filename,
                        dc.page_number,
                        dc.chunk_index,
                        dc.chunk_text
                    FROM document_chunks dc
                    JOIN documents d
                        ON d.id = dc.document_id
                    ORDER BY dc.document_id, dc.chunk_index
                    """
                )

                return cursor.fetchall()

    finally:
        connection.close()