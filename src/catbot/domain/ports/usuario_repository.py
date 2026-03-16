from abc import ABC, abstractmethod
from uuid import UUID

from catbot.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    async def get_by_id(self, usuario_id: UUID) -> Usuario | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Usuario | None: ...

    @abstractmethod
    async def save(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    async def list_all(self) -> list[Usuario]: ...

    @abstractmethod
    async def delete(self, usuario_id: UUID) -> None: ...
