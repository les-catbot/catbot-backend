from uuid import UUID

from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem
from catbot.domain.ports.conversa_repository import ConversaRepository


class InMemoryConversaRepository(ConversaRepository):
    def __init__(self) -> None:
        self._conversas: dict[UUID, Conversa] = {}
        self._mensagens: dict[UUID, list[Mensagem]] = {}

    async def get_by_id(self, conversa_id: UUID) -> Conversa | None:
        return self._conversas.get(conversa_id)

    async def save(self, conversa: Conversa) -> Conversa:
        self._conversas[conversa.id] = conversa
        if conversa.id not in self._mensagens:
            self._mensagens[conversa.id] = []
        return conversa

    async def list_by_usuario(self, usuario_id: UUID) -> list[Conversa]:
        return [c for c in self._conversas.values() if c.usuario_id == usuario_id]

    async def add_mensagem(self, mensagem: Mensagem) -> Mensagem:
        if mensagem.conversa_id not in self._mensagens:
            self._mensagens[mensagem.conversa_id] = []
        self._mensagens[mensagem.conversa_id].append(mensagem)
        return mensagem

    async def get_mensagens(self, conversa_id: UUID) -> list[Mensagem]:
        return list(self._mensagens.get(conversa_id, []))
