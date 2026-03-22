"""Stub embedding service para desenvolvimento local sem modelo real."""

import hashlib
import math

from catbot.domain.ports.embedding_service import EmbeddingService

STUB_DIMENSION = 384


class StubEmbeddingService(EmbeddingService):
    """Generates deterministic pseudo-embeddings derived from the text hash.

    Useful for local development and tests — the vectors are stable (same text
    always returns the same vector) so similarity comparisons are meaningful
    even without a real model.
    """

    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [self._pseudo_embed(t) for t in texts]

    def dimension(self) -> int:
        return STUB_DIMENSION

    @staticmethod
    def _pseudo_embed(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).hexdigest()
        raw = [int(digest[i : i + 2], 16) / 255.0 for i in range(0, len(digest), 2)]
        while len(raw) < STUB_DIMENSION:
            raw = raw + raw
        raw = raw[:STUB_DIMENSION]
        norm = math.sqrt(sum(x * x for x in raw))
        return [x / norm for x in raw] if norm > 0 else raw
