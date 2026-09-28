import pymupdf


def extract_pages_from_pdf(file_path: str) -> list[dict]:
    """
    Extract text page-by-page so we can preserve page numbers
    for citations.
    """

    document = pymupdf.open(file_path)

    pages = []

    try:
        for page_index, page in enumerate(document):
            text = page.get_text("text").strip()

            if text:
                pages.append(
                    {
                        "page_number": page_index + 1,
                        "text": text,
                    }
                )
    finally:
        document.close()

    return pages


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    text = text.strip()

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def chunk_pdf_pages(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """
    Chunk every PDF page separately.

    This lets each chunk retain its original page number.
    """

    all_chunks = []

    chunk_index = 0

    for page in pages:
        page_number = page["page_number"]
        page_text = page["text"]

        page_chunks = chunk_text(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for chunk in page_chunks:
            all_chunks.append(
                {
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "text": chunk,
                }
            )

            chunk_index += 1

    return all_chunks
