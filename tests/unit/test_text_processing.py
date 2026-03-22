"""Testes para extração de texto e chunking."""

import pytest

from catbot.application.text_processing import chunk_text, extract_text


class TestExtractText:
    def test_raw_text(self):
        result = extract_text(None, None, "  Hello world  ")
        assert result == "Hello world"

    def test_txt_file(self):
        content = b"Texto de exemplo.\r\nSegunda linha."
        result = extract_text(content, "doc.txt", None)
        assert "Texto de exemplo." in result
        assert "\r\n" not in result

    def test_md_file(self):
        content = b"# Titulo\n\nConteudo aqui."
        result = extract_text(content, "readme.md", None)
        assert "Titulo" in result

    def test_unsupported_format(self):
        with pytest.raises(ValueError, match="não suportado"):
            extract_text(b"binary", "image.png", None)

    def test_no_input(self):
        with pytest.raises(ValueError, match="Forneça"):
            extract_text(None, None, None)

    def test_raw_text_takes_precedence(self):
        result = extract_text(b"file content", "doc.txt", "raw text")
        assert result == "raw text"


class TestChunkText:
    def test_empty_text(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        text = "Uma frase curta."
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_multiple_chunks(self):
        sentences = ["Frase numero {}.".format(i) for i in range(50)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=100, overlap=30)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_overlap_preserves_context(self):
        text = "Primeira sentença aqui. Segunda sentença aqui. Terceira sentença aqui."
        chunks = chunk_text(text, chunk_size=40, overlap=20)
        assert len(chunks) >= 2

    def test_all_text_covered(self):
        sentences = ["Sentença {}.".format(i) for i in range(20)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=80, overlap=20)
        full_text = " ".join(chunks)
        for sentence in sentences:
            assert sentence in full_text
