"""Embedding service backed by Ollama's /api/embed endpoint."""

import httpx

from catbot.domain.ports.embedding_service import EmbeddingService


class OllamaEmbeddingService(EmbeddingService):
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",  # Voltamos ao modelo de grande capacidade
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._dimension: int | None = None

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embed",
                json={
                    "model": self._model,
                    "input": texts,
                    "truncate": True  # Apenas como cinto de segurança
                },
            )
            response.raise_for_status()
            data = response.json()

        embeddings: list[list[float]] = data["embeddings"]
        if self._dimension is None and embeddings:
            self._dimension = len(embeddings[0])
        return embeddings

    def dimension(self) -> int:
        if self._dimension is not None:
            return self._dimension
        return 768  # nomic-embed-text usa dimensão 768