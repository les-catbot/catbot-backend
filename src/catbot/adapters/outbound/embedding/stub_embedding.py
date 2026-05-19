"""Embedding service deterministic for tests and local smoke checks."""

from catbot.domain.ports.embedding_service import EmbeddingService


class StubEmbeddingService(EmbeddingService):
    def __init__(self, dimensions: int = 16) -> None:
        self._dimensions = dimensions

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def dimension(self) -> int:
        return self._dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for index, char in enumerate(text.lower()):
            bucket = (ord(char) + index) % self._dimensions
            vector[bucket] += 1.0
        return vector
