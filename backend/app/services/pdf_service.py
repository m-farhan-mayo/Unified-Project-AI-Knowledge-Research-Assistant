import fitz


def extract_text_from_pdf(file_path: str) -> str:
    document = fitz.open(file_path)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks