from uuid import UUID

from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem
from catbot.domain.entities.resposta import FonteResposta, Resposta
from catbot.domain.ports.conversa_repository import ConversaRepository


class InMemoryConversaRepository(ConversaRepository):
    def __init__(self) -> None:
        self._conversas: dict[UUID, Conversa] = {}
        self._mensagens: dict[UUID, list[Mensagem]] = {}
        self._respostas: dict[UUID, Resposta] = {}
        self._fontes: dict[UUID, list[FonteResposta]] = {}

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
        # Retorna a lista de mensagens atreladas a esta conversa na ordem de inserção
        return list(self._mensagens.get(conversa_id, []))

    async def save_resposta(self, resposta: Resposta) -> Resposta:
        self._respostas[resposta.id] = resposta
        return resposta

    async def add_fonte_resposta(self, fonte: FonteResposta) -> FonteResposta:
        self._fontes.setdefault(fonte.resposta_id, []).append(fonte)
        return fonte

    async def get_fontes_por_mensagem(self, mensagem_id: UUID) -> list[FonteResposta]:
        resposta = next(
            (r for r in self._respostas.values() if r.mensagem_id == mensagem_id),
            None,
        )
        if resposta is None:
            return []
        return list(self._fontes.get(resposta.id, []))

    async def list_all(self) -> list[Conversa]:
        return list(self._conversas.values())
