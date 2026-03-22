"""Utilitários de extração de texto e chunking para a base de conhecimento."""

import io
import re


def extract_text(file_content: bytes | None, filename: str | None, raw_text: str | None) -> str:
    """Extract clean text from a file or raw input.

    Exactly one of (file_content + filename) or raw_text must be provided.
    Raises ValueError when the input cannot be processed.
    """
    if raw_text:
        return _clean(raw_text)

    if file_content is None or filename is None:
        raise ValueError("Forneça um arquivo (com nome) ou texto bruto.")

    ext = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        return _extract_pdf(file_content)
    if ext in {"txt", "md", "csv", "text"}:
        return _clean(file_content.decode("utf-8", errors="replace"))

    raise ValueError(f"Formato de arquivo não suportado: .{ext}")


def _extract_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return _clean("\n".join(pages))


def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    """Split text into overlapping chunks, respecting sentence boundaries.

    Args:
        text: The full text to split.
        chunk_size: Target number of characters per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        Ordered list of text chunks. Empty list if the input is blank.
    """
    if not text.strip():
        return []

    sentences = _split_sentences(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_len + sentence_len > chunk_size and current:
            chunks.append(" ".join(current))
            overlap_text = " ".join(current)
            _keep = _tail_within(overlap_text, overlap)
            current = [_keep] if _keep else []
            current_len = len(_keep) if _keep else 0

        current.append(sentence)
        current_len += sentence_len + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Heuristic sentence splitter that handles common abbreviations."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if s.strip()]


def _tail_within(text: str, max_chars: int) -> str:
    """Return the rightmost portion of *text* fitting within *max_chars*,
    aligned to a sentence boundary when possible."""
    if len(text) <= max_chars:
        return text
    tail = text[-max_chars:]
    boundary = tail.find(". ")
    if boundary != -1:
        return tail[boundary + 2 :]
    return tail
