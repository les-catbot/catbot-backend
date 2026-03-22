import math
import struct
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catbot.adapters.outbound.persistence.sqlalchemy.models import ChunkDocumentoModel
from catbot.domain.entities.chunk_documento import ChunkDocumento
from catbot.domain.ports.vector_repository import VectorRepository


def _floats_to_bytes(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _bytes_to_floats(raw: bytes) -> list[float]:
    count = len(raw) // 4
    return list(struct.unpack(f"{count}f", raw))


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SQLAlchemyVectorRepository(VectorRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def save_chunks(self, chunks: list[ChunkDocumento]) -> list[ChunkDocumento]:
        async with self._sf() as session:
            rows = [
                ChunkDocumentoModel(
                    id=c.id,
                    documento_id=c.documento_id,
                    versao_id=c.versao_id,
                    conteudo=c.conteudo,
                    indice_chunk=c.indice_chunk,
                    embedding=_floats_to_bytes(c.embedding),
                    categoria=c.categoria,
                    fonte=c.fonte,
                )
                for c in chunks
            ]
            session.add_all(rows)
            await session.commit()
        return chunks

    async def delete_by_documento(self, documento_id: UUID) -> int:
        async with self._sf() as session:
            result = await session.execute(
                delete(ChunkDocumentoModel).where(
                    ChunkDocumentoModel.documento_id == documento_id
                )
            )
            await session.commit()
            return result.rowcount

    async def delete_by_versao(self, versao_id: UUID) -> int:
        async with self._sf() as session:
            result = await session.execute(
                delete(ChunkDocumentoModel).where(
                    ChunkDocumentoModel.versao_id == versao_id
                )
            )
            await session.commit()
            return result.rowcount

    async def search_similar(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[ChunkDocumento]:
        async with self._sf() as session:
            result = await session.execute(select(ChunkDocumentoModel))
            all_rows = result.scalars().all()

        scored = [
            (_to_entity(row), _cosine_similarity(query_embedding, _bytes_to_floats(row.embedding)))
            for row in all_rows
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored[:top_k]]

    async def get_by_documento(self, documento_id: UUID) -> list[ChunkDocumento]:
        async with self._sf() as session:
            result = await session.execute(
                select(ChunkDocumentoModel)
                .where(ChunkDocumentoModel.documento_id == documento_id)
                .order_by(ChunkDocumentoModel.indice_chunk)
            )
            return [_to_entity(r) for r in result.scalars().all()]


def _to_entity(row: ChunkDocumentoModel) -> ChunkDocumento:
    return ChunkDocumento(
        id=row.id,
        documento_id=row.documento_id,
        versao_id=row.versao_id,
        conteudo=row.conteudo,
        indice_chunk=row.indice_chunk,
        embedding=_bytes_to_floats(row.embedding),
        categoria=row.categoria,
        fonte=row.fonte,
        criado_em=row.criado_em,
    )
