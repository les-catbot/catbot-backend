"""In-memory vector repository for development and testing."""

import math
from uuid import UUID

from catbot.domain.entities.chunk_documento import ChunkDocumento
from catbot.domain.ports.vector_repository import VectorRepository


class InMemoryVectorRepository(VectorRepository):
    def __init__(self) -> None:
        self._chunks: dict[UUID, ChunkDocumento] = {}

    async def save_chunks(self, chunks: list[ChunkDocumento]) -> list[ChunkDocumento]:
        for chunk in chunks:
            self._chunks[chunk.id] = chunk
        return chunks

    async def delete_by_documento(self, documento_id: UUID) -> int:
        to_delete = [
            cid for cid, c in self._chunks.items() if c.documento_id == documento_id
        ]
        for cid in to_delete:
            del self._chunks[cid]
        return len(to_delete)

    async def delete_by_versao(self, versao_id: UUID) -> int:
        to_delete = [
            cid for cid, c in self._chunks.items() if c.versao_id == versao_id
        ]
        for cid in to_delete:
            del self._chunks[cid]
        return len(to_delete)

    async def search_similar(
        self,
        query_embedding: list[float],
        categoria: str | None = None,
        top_k: int = 5,
    ) -> list[ChunkDocumento]:
        chunks = self._chunks.values()
        if categoria:
            chunks = [chunk for chunk in chunks if chunk.categoria == categoria]

        scored = [
            (c, _cosine_similarity(query_embedding, c.embedding))
            for c in chunks
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    async def get_by_documento(self, documento_id: UUID) -> list[ChunkDocumento]:
        return [
            c for c in self._chunks.values() if c.documento_id == documento_id
        ]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
