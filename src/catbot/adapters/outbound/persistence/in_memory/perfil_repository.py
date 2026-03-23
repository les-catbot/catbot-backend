from uuid import UUID
from catbot.domain.entities.perfil import Perfil
from catbot.domain.ports.perfil_repository import PerfilRepository

class InMemoryPerfilRepository(PerfilRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Perfil] = {}

    async def get_by_id(self, perfil_id: UUID) -> Perfil | None:
        return self._store.get(perfil_id)

    async def list_all(self) -> list[Perfil]:
        return list(self._store.values())

    async def save(self, perfil: Perfil) -> Perfil:
        self._store[perfil.id] = perfil
        return perfil