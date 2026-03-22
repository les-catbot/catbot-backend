from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catbot.adapters.outbound.persistence.sqlalchemy.models import AvaliacaoModel
from catbot.domain.entities.avaliacao import Avaliacao
from catbot.domain.ports.avaliacao_repository import AvaliacaoRepository


class SQLAlchemyAvaliacaoRepository(AvaliacaoRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def save(self, avaliacao: Avaliacao) -> Avaliacao:
        async with self._sf() as session:
            row = AvaliacaoModel(
                id=avaliacao.id,
                mensagem_id=avaliacao.mensagem_id,
                usuario_id=avaliacao.usuario_id,
                nota=avaliacao.nota,
                comentario=avaliacao.comentario,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_entity(row)

    async def get_by_mensagem(self, mensagem_id: UUID) -> list[Avaliacao]:
        async with self._sf() as session:
            result = await session.execute(
                select(AvaliacaoModel).where(AvaliacaoModel.mensagem_id == mensagem_id)
            )
            return [_to_entity(r) for r in result.scalars().all()]

    async def list_all(self) -> list[Avaliacao]:
        async with self._sf() as session:
            result = await session.execute(select(AvaliacaoModel))
            return [_to_entity(r) for r in result.scalars().all()]


def _to_entity(row: AvaliacaoModel) -> Avaliacao:
    return Avaliacao(
        id=row.id,
        mensagem_id=row.mensagem_id,
        usuario_id=row.usuario_id,
        nota=row.nota,
        comentario=row.comentario,
        criado_em=row.criado_em,
    )
