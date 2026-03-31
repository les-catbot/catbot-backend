from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catbot.adapters.outbound.persistence.sqlalchemy.models import UsuarioModel
from catbot.domain.entities.usuario import Usuario
from catbot.domain.entities.perfil import Perfil
from catbot.domain.ports.usuario_repository import UsuarioRepository


class SQLAlchemyUsuarioRepository(UsuarioRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        async with self._sf() as session:
            # Usamos selectinload para pedir ao Postgres que traga também o Perfil associado
            stmt = select(UsuarioModel).options(selectinload(UsuarioModel.perfil)).where(UsuarioModel.id == usuario_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> Usuario | None:
        async with self._sf() as session:
            stmt = select(UsuarioModel).options(selectinload(UsuarioModel.perfil)).where(UsuarioModel.email == email)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
            return _to_entity(row) if row else None

    async def save(self, usuario: Usuario) -> Usuario:
        async with self._sf() as session:
            row = UsuarioModel(
                id=usuario.id,
                nome=usuario.nome,
                email=usuario.email,
                senha_hash=usuario.senha_hash,
                perfil_id=usuario.perfil_id,
            )
            # Utilizamos MERGE em vez de ADD.
            # Se o ID já existir, faz UPDATE. Se não existir, faz INSERT.
            row = await session.merge(row)
            await session.commit()

            # Recarregamos com as relações preenchidas
            stmt = select(UsuarioModel).options(selectinload(UsuarioModel.perfil)).where(UsuarioModel.id == row.id)
            result = await session.execute(stmt)
            row_atualizada = result.scalar_one()

            return _to_entity(row_atualizada)

    async def list_all(self) -> list[Usuario]:
        async with self._sf() as session:
            stmt = select(UsuarioModel).options(selectinload(UsuarioModel.perfil))
            result = await session.execute(stmt)
            return [_to_entity(r) for r in result.scalars().all()]

    async def delete(self, usuario_id: UUID) -> None:
        async with self._sf() as session:
            await session.execute(
                delete(UsuarioModel).where(UsuarioModel.id == usuario_id)
            )
            await session.commit()


def _to_entity(row: UsuarioModel) -> Usuario:
    # Mapeamos o Perfil se ele vier carregado da base de dados
    perfil_entity = None
    if getattr(row, "perfil", None):
        perfil_entity = Perfil(
            id=row.perfil.id,
            nome=row.perfil.nome,
            descricao=row.perfil.descricao
        )

    return Usuario(
        id=row.id,
        nome=row.nome,
        email=row.email,
        senha_hash=row.senha_hash,
        perfil_id=row.perfil_id,
        perfil=perfil_entity,
        criado_em=row.criado_em,
    )