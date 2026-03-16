"""Caso de uso: Realizar Pergunta em Linguagem Natural."""

from dataclasses import dataclass
from uuid import UUID

from catbot.domain.entities.mensagem import Mensagem, StatusValidacao, TipoRemetente
from catbot.domain.entities.resposta import Resposta
from catbot.domain.ports.conversa_repository import ConversaRepository
from catbot.domain.ports.llm_client import LLMClient
from catbot.domain.ports.nlp_processor import NLPProcessor


@dataclass
class ChatResult:
    resposta: str
    confianca: float
    mensagem_id: UUID


class ChatService:
    def __init__(
        self,
        conversa_repo: ConversaRepository,
        nlp_processor: NLPProcessor,
        llm_client: LLMClient,
    ) -> None:
        self._conversa_repo = conversa_repo
        self._nlp = nlp_processor
        self._llm = llm_client

    async def processar_pergunta(
        self,
        conversa_id: UUID,
        texto_usuario: str,
    ) -> ChatResult:
        if not texto_usuario or not texto_usuario.strip():
            raise ValueError("A pergunta não pode estar vazia.")

        msg_usuario = Mensagem(
            conversa_id=conversa_id,
            conteudo=texto_usuario.strip(),
            tipo_remetente=TipoRemetente.USUARIO,
            status_validacao=StatusValidacao.VALIDA,
        )
        msg_usuario = await self._conversa_repo.add_mensagem(msg_usuario)

        nlp_result = await self._nlp.process(msg_usuario.conteudo)

        context = f"Intenção: {nlp_result.intencao or 'desconhecida'}\n"
        context += f"Entidades: {nlp_result.entidades}\n"
        context += f"Tokens: {nlp_result.tokens}"

        llm_response = await self._llm.generate(
            prompt=msg_usuario.conteudo,
            context=context,
        )

        msg_bot = Mensagem(
            conversa_id=conversa_id,
            conteudo=llm_response.texto,
            tipo_remetente=TipoRemetente.BOT,
            status_validacao=StatusValidacao.VALIDA,
        )
        msg_bot = await self._conversa_repo.add_mensagem(msg_bot)

        resposta = Resposta(
            mensagem_id=msg_bot.id,
            texto_resposta=llm_response.texto,
            pontuacao_confianca=llm_response.confianca,
        )
        _ = resposta  # TODO: persistir resposta quando o repositório estiver pronto

        return ChatResult(
            resposta=llm_response.texto,
            confianca=llm_response.confianca,
            mensagem_id=msg_bot.id,
        )
