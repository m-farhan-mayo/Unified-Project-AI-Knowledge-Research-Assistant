import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def get_embedding(text: str):
    client = genai.Client(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )

    return response.embeddings[0].values


def get_embeddings_for_chunks(chunks: list[str]):
    embeddings = []

    for chunk in chunks:
        vector = get_embedding(chunk)
        embeddings.append(vector)

    return embeddings