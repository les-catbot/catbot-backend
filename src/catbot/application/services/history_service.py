"""Caso de uso: Consultar Histórico de Conversas."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem
from catbot.domain.ports.conversa_repository import ConversaRepository


@dataclass
class ConversaComMensagens:
    conversa: Conversa
    mensagens: list[Mensagem]


class HistoryService:
    def __init__(self, conversa_repo: ConversaRepository) -> None:
        self._repo = conversa_repo

    async def listar_conversas(self, usuario_id: UUID) -> list[Conversa]:
        return await self._repo.list_by_usuario(usuario_id)

    async def detalhar_conversa(self, conversa_id: UUID) -> ConversaComMensagens:
        conversa = await self._repo.get_by_id(conversa_id)
        if conversa is None:
            raise ValueError("Conversa não encontrada.")

        mensagens = await self._repo.get_mensagens(conversa_id)
        return ConversaComMensagens(conversa=conversa, mensagens=mensagens)

    async def filtrar_por_periodo(
        self,
        usuario_id: UUID,
        inicio: datetime,
        fim: datetime,
    ) -> list[Conversa]:
        todas = await self._repo.list_by_usuario(usuario_id)
        return [c for c in todas if inicio <= c.iniciado_em <= fim]
