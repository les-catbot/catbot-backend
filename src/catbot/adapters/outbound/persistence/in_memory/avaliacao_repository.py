from uuid import UUID

from catbot.domain.entities.avaliacao import Avaliacao
from catbot.domain.ports.avaliacao_repository import AvaliacaoRepository


class InMemoryAvaliacaoRepository(AvaliacaoRepository):
    def __init__(self) -> None:
        self._store: dict[UUID, Avaliacao] = {}

    async def save(self, avaliacao: Avaliacao) -> Avaliacao:
        self._store[avaliacao.id] = avaliacao
        return avaliacao

    async def get_by_mensagem(self, mensagem_id: UUID) -> list[Avaliacao]:
        return [a for a in self._store.values() if a.mensagem_id == mensagem_id]

    async def list_all(self) -> list[Avaliacao]:
        return list(self._store.values())
