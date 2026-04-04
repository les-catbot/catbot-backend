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
        kb_service: KnowledgeBaseService,
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

        # 1. Processamento NLP Híbrido (Intenção e Entidades)
        nlp_result = await self._nlp.process(msg_usuario.conteudo)

        print(f"\n[DEBUG NLP] Intenção detectada: {nlp_result.intencao}")
        print(f"[DEBUG NLP] Entidades: {nlp_result.entidades}")

        # Se for apenas saudação, podemos pular a busca no Vector DB e responder direto
        if nlp_result.intencao == "SAUDACAO_OU_OUTROS":
            llm_response = await self._llm.generate(
                prompt=msg_usuario.conteudo,
                context="Intenção: SAUDACAO_OU_OUTROS. Responda educadamente como CatBot, o assistente do IFES."
            )
        else:
            # 2. Busca Semântica Enriquecida no Banco Vetorial
            query_busca = msg_usuario.conteudo
            if nlp_result.entidades:
                termos_entidades = " ".join(str(v) for v in nlp_result.entidades.values())
                # Junta a intenção, os termos extraídos e a pergunta original para uma busca fortíssima
                query_busca = f"{nlp_result.intencao} {termos_entidades} {msg_usuario.conteudo}"
                print(f"[DEBUG RAG] Query Vetorial: {query_busca}")

            chunks_relevantes = await self._kb.buscar_similar(query_busca, top_k=self._rag_top_k)

            print(f"[DEBUG RAG] Encontrou {len(chunks_relevantes)} pedaços de texto no banco.")
            if chunks_relevantes:
                print(f"[DEBUG RAG] Melhor texto encontrado: {chunks_relevantes[0].conteudo[:150]}...")

            # 3. Montagem do Contexto (Memória) para o LLM
            context = f"Intenção detectada do usuário: {nlp_result.intencao}\n"
            context += f"Entidades identificadas: {nlp_result.entidades}\n\n"

            if chunks_relevantes:
                context += "INFORMAÇÕES RECUPERADAS DA BASE DE CONHECIMENTO DO IFES:\n"
                for i, chunk in enumerate(chunks_relevantes, 1):
                    context += f"--- Documento {i} (Fonte: {chunk.fonte}) ---\n{chunk.conteudo}\n\n"
            else:
                context += "Nenhuma informação relevante encontrada na base de conhecimento para essa pergunta.\n\n"

            # 4. Geração da Resposta com RAG
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