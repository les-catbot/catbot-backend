"""Caso de uso: Realizar Pergunta em Linguagem Natural."""

from dataclasses import dataclass
from uuid import UUID

from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem, StatusValidacao, TipoRemetente
from catbot.domain.entities.resposta import Resposta
from catbot.domain.ports.conversa_repository import ConversaRepository
from catbot.domain.ports.llm_client import LLMClient
from catbot.domain.ports.nlp_processor import NLPProcessor
from catbot.application.services.knowledge_base_service import KnowledgeBaseService


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
        kb_service: KnowledgeBaseService,  # NOVO: Injetando o motor de busca
        rag_top_k: int = 5,
    ) -> None:
        self._conversa_repo = conversa_repo
        self._nlp = nlp_processor
        self._llm = llm_client
        self._kb = kb_service
        self._rag_top_k = rag_top_k

    async def iniciar_conversa(self, usuario_id: UUID) -> Conversa:
        """Inicia uma nova sessão de chat para o usuário."""
        nova_conversa = Conversa(usuario_id=usuario_id)
        return await self._conversa_repo.save(nova_conversa)

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

        # 1. Processamento NLP para entender intenção
        nlp_result = await self._nlp.process(msg_usuario.conteudo)

        # 2. Busca Semântica no Banco Vetorial (O coração do RAG)
        # Traz os 3 blocos de texto mais similares à pergunta do utilizador
        chunks_relevantes = await self._kb.buscar_similar(msg_usuario.conteudo, top_k=self._rag_top_k)

        # 3. Montagem do Contexto (Memória) para o LLM
        context = f"Intenção detectada: {nlp_result.intencao or 'desconhecida'}\n\n"

        if chunks_relevantes:
            context += "INFORMAÇÕES RECUPERADAS DA BASE DE CONHECIMENTO:\n"
            for i, chunk in enumerate(chunks_relevantes, 1):
                context += f"--- Documento {i} (Fonte: {chunk.fonte}) ---\n{chunk.conteudo}\n\n"
        else:
            context += "Nenhuma informação relevante encontrada na base de conhecimento.\n\n"

        # 4. Geração da Resposta pela Inteligência Artificial
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
        await self._conversa_repo.save_resposta(resposta)

        return ChatResult(
            resposta=llm_response.texto,
            confianca=llm_response.confianca,
            mensagem_id=msg_bot.id,
        )