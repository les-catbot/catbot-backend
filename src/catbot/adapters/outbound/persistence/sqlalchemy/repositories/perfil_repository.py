import uuid
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from catbot.adapters.outbound.persistence.sqlalchemy.models import PerfilModel
from catbot.domain.entities.perfil import Perfil
from catbot.domain.ports.perfil_repository import PerfilRepository


class SQLAlchemyPerfilRepository(PerfilRepository):
    """Implementação definitiva do repositório de Perfis usando SQLAlchemy assíncrono."""

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory

    def _to_domain(self, model: PerfilModel) -> Perfil:
        """Converte o modelo do banco (ORM) para a entidade de domínio puro."""
        return Perfil(
            id=model.id,
            nome=model.nome,
            descricao=model.descricao,
        )

    async def get_by_id(self, perfil_id: uuid.UUID) -> Perfil | None:
        async with self._session_factory() as session:
            stmt = select(PerfilModel).where(PerfilModel.id == perfil_id)
            result = await session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return self._to_domain(model)
            return None

    async def list_all(self) -> list[Perfil]:
        async with self._session_factory() as session:
            stmt = select(PerfilModel)
            result = await session.execute(stmt)
            models = result.scalars().all()

            return [self._to_domain(m) for m in models]

    async def save(self, perfil: Perfil) -> Perfil:
        async with self._session_factory() as session:
            model = PerfilModel(
                id=perfil.id,
                nome=perfil.nome,
                descricao=perfil.descricao,
            )
            # Usamos merge em vez de add para suportar tanto Inserção (Create) quanto Atualização (Update)
            model = await session.merge(model)
            await session.commit()
            return self._to_domain(model)