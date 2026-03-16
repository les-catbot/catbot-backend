from abc import ABC, abstractmethod
from uuid import UUID

from catbot.domain.entities.avaliacao import Avaliacao


class AvaliacaoRepository(ABC):
    @abstractmethod
    async def save(self, avaliacao: Avaliacao) -> Avaliacao: ...

    @abstractmethod
    async def get_by_mensagem(self, mensagem_id: UUID) -> list[Avaliacao]: ...

    @abstractmethod
    async def list_all(self) -> list[Avaliacao]: ...
