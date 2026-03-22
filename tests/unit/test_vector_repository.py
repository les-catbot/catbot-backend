"""Testes para o InMemoryVectorRepository."""

from uuid import uuid4

import pytest

from catbot.adapters.outbound.persistence.in_memory import InMemoryVectorRepository
from catbot.domain.entities.chunk_documento import ChunkDocumento


@pytest.fixture
def repo():
    return InMemoryVectorRepository()


def _make_chunk(doc_id=None, versao_id=None, embedding=None, idx=0):
    return ChunkDocumento(
        documento_id=doc_id or uuid4(),
        versao_id=versao_id or uuid4(),
        conteudo=f"Chunk de teste número {idx}",
        indice_chunk=idx,
        embedding=embedding or [0.1 * (idx + 1)] * 10,
        categoria="cat",
        fonte="src",
    )


class TestSaveAndRetrieve:
    async def test_save_and_get_by_documento(self, repo):
        doc_id = uuid4()
        chunks = [_make_chunk(doc_id=doc_id, idx=i) for i in range(3)]
        await repo.save_chunks(chunks)

        result = await repo.get_by_documento(doc_id)
        assert len(result) == 3

    async def test_save_returns_chunks(self, repo):
        chunks = [_make_chunk(idx=0)]
        result = await repo.save_chunks(chunks)
        assert result[0].id == chunks[0].id


class TestDelete:
    async def test_delete_by_documento(self, repo):
        doc_id = uuid4()
        chunks = [_make_chunk(doc_id=doc_id, idx=i) for i in range(5)]
        await repo.save_chunks(chunks)

        count = await repo.delete_by_documento(doc_id)
        assert count == 5
        assert await repo.get_by_documento(doc_id) == []

    async def test_delete_by_versao(self, repo):
        doc_id = uuid4()
        v1 = uuid4()
        v2 = uuid4()
        chunks_v1 = [_make_chunk(doc_id=doc_id, versao_id=v1, idx=i) for i in range(3)]
        chunks_v2 = [_make_chunk(doc_id=doc_id, versao_id=v2, idx=i) for i in range(2)]
        await repo.save_chunks(chunks_v1 + chunks_v2)

        count = await repo.delete_by_versao(v1)
        assert count == 3
        remaining = await repo.get_by_documento(doc_id)
        assert len(remaining) == 2


class TestSimilaritySearch:
    async def test_search_returns_ordered_by_similarity(self, repo):
        doc_id = uuid4()
        c1 = _make_chunk(doc_id=doc_id, embedding=[1.0, 0.0, 0.0], idx=0)
        c2 = _make_chunk(doc_id=doc_id, embedding=[0.0, 1.0, 0.0], idx=1)
        c3 = _make_chunk(doc_id=doc_id, embedding=[0.9, 0.1, 0.0], idx=2)
        await repo.save_chunks([c1, c2, c3])

        results = await repo.search_similar([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0].indice_chunk in (0, 2)

    async def test_search_empty_repo(self, repo):
        results = await repo.search_similar([1.0, 0.0], top_k=5)
        assert results == []
