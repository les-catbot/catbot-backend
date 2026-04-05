from abc import ABC, abstractmethod
from uuid import UUID

from catbot.domain.entities.chunk_documento import ChunkDocumento


class VectorRepository(ABC):
    @abstractmethod
    async def save_chunks(self, chunks: list[ChunkDocumento]) -> list[ChunkDocumento]:
        """Persist a batch of chunks atomically. Returns the saved chunks."""
        ...

    @abstractmethod
    async def delete_by_documento(self, documento_id: UUID) -> int:
        """Remove all chunks for a document. Returns count of deleted chunks."""
        ...

    @abstractmethod
    async def delete_by_versao(self, versao_id: UUID) -> int:
        """Remove all chunks for a specific document version."""
        ...

    @abstractmethod
    async def search_similar(self, query_embedding: list[float], categoria: str | None = None, top_k: int = 5) -> list[
        ChunkDocumento]:
        """Return the top_k most similar chunks by cosine similarity."""
        ...

    @abstractmethod
    async def get_by_documento(self, documento_id: UUID) -> list[ChunkDocumento]:
        """Return all chunks belonging to a document."""
        ...
