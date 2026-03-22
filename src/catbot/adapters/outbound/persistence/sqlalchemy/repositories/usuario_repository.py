from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from catbot.adapters.outbound.persistence.sqlalchemy.models import UsuarioModel
from catbot.domain.entities.usuario import Usuario
from catbot.domain.ports.usuario_repository import UsuarioRepository


class SQLAlchemyUsuarioRepository(UsuarioRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        async with self._sf() as session:
            row = await session.get(UsuarioModel, usuario_id)
            return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> Usuario | None:
        async with self._sf() as session:
            result = await session.execute(
                select(UsuarioModel).where(UsuarioModel.email == email)
            )
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
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _to_entity(row)

    async def list_all(self) -> list[Usuario]:
        async with self._sf() as session:
            result = await session.execute(select(UsuarioModel))
            return [_to_entity(r) for r in result.scalars().all()]

    async def delete(self, usuario_id: UUID) -> None:
        async with self._sf() as session:
            await session.execute(
                delete(UsuarioModel).where(UsuarioModel.id == usuario_id)
            )
            await session.commit()


def _to_entity(row: UsuarioModel) -> Usuario:
    return Usuario(
        id=row.id,
        nome=row.nome,
        email=row.email,
        senha_hash=row.senha_hash,
        perfil_id=row.perfil_id,
        criado_em=row.criado_em,
    )
