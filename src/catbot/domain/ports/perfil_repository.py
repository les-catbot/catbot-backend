from abc import ABC, abstractmethod
from uuid import UUID
from catbot.domain.entities.perfil import Perfil

class PerfilRepository(ABC):
    @abstractmethod
    async def get_by_id(self, perfil_id: UUID) -> Perfil | None: ...

    @abstractmethod
    async def list_all(self) -> list[Perfil]: ...

    @abstractmethod
    async def save(self, perfil: Perfil) -> Perfil: ...