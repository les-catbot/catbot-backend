"""Utilitários de extração de texto e chunking para a base de conhecimento."""

import io
import re

def extract_text(file_content: bytes | None, filename: str | None, raw_text: str | None) -> str:
    """Extract clean text from a file or raw input."""
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
    chunk_size: int = 800,
    overlap: int = 200,
) -> list[str]:
    """
    Divide o texto em chunks (pedaços) baseados em tamanho de caracteres,
    mas garante que o corte ocorra em limites de palavras (espaços) para não quebrar a semântica.
    """
    if not text.strip():
        return []

    # Divide o texto em palavras para evitar cortes no meio de uma palavra
    words = text.split(" ")
    chunks: list[str] = []

    current_chunk_words: list[str] = []
    current_length = 0

    # Heurística para manter a proporção de overlap em palavras (tamanho médio de palavra = 6 caracteres)
    overlap_words_count = max(1, overlap // 6)

    for word in words:
        word_len = len(word) + 1  # +1 para o espaço

        if current_length + word_len > chunk_size and current_chunk_words:
            # Salva o chunk atual
            chunks.append(" ".join(current_chunk_words))

            # Prepara o próximo chunk pegando o overlap do final do chunk anterior
            current_chunk_words = current_chunk_words[-overlap_words_count:]
            current_length = sum(len(w) + 1 for w in current_chunk_words)

        current_chunk_words.append(word)
        current_length += word_len

    # Adiciona o último pedaço, se sobrar algo
    if current_chunk_words:
        chunks.append(" ".join(current_chunk_words))

    return chunks