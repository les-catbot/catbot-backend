from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catbot.adapters.outbound.persistence.sqlalchemy.models import ChunkDocumentoModel
from catbot.domain.entities.chunk_documento import ChunkDocumento
from catbot.domain.ports.vector_repository import VectorRepository


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
                    embedding=c.embedding,
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
            self, query_embedding: list[float], categoria: str | None = None, top_k: int = 5
    ) -> list[ChunkDocumento]:
        async with self._sf() as session:
            stmt = select(ChunkDocumentoModel)

            # --- FILTRO SEMÂNTICO (PRE-FILTERING) ---
            # Filtra pela categoria ANTES de fazer o cálculo matemático de vetores
            if categoria:
                stmt = stmt.where(ChunkDocumentoModel.categoria == categoria)

            # Calcula a similaridade do cosseno e limita aos top_k
            stmt = stmt.order_by(
                ChunkDocumentoModel.embedding.cosine_distance(query_embedding)
            ).limit(top_k)

            result = await session.execute(stmt)
            return [_to_entity(r) for r in result.scalars().all()]

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
        embedding=list(row.embedding),
        categoria=row.categoria,
        fonte=row.fonte,
        criado_em=row.criado_em,
    )