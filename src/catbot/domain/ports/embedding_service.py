from abc import ABC, abstractmethod


class EmbeddingService(ABC):
    @abstractmethod
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a list of text chunks."""
        ...

    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors produced."""
        ...
