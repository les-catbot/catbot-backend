from uuid import UUID

from catbot.domain.entities.usuario import Usuario
from catbot.domain.ports.usuario_repository import UsuarioRepository


class InMemoryUsuarioRepository(UsuarioRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Usuario] = {}

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        return self._store.get(usuario_id)

    async def get_by_email(self, email: str) -> Usuario | None:
        return next((u for u in self._store.values() if u.email == email), None)

    async def save(self, usuario: Usuario) -> Usuario:
        self._store[usuario.id] = usuario
        return usuario

    async def list_all(self) -> list[Usuario]:
        return list(self._store.values())

    async def delete(self, usuario_id: UUID) -> None:
        self._store.pop(usuario_id, None)
