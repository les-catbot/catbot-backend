"""Caso de uso: Realizar Pergunta em Linguagem Natural com Histórico (Memória)."""

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
        rag_top_k: int = 4, # Reduzido para 4 para manter o LLM focado
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

    def _montar_contexto(self, chunks_relevantes: list, ultimas_mensagens: list, intencao: str) -> str:
        """Função auxiliar para organizar visualmente o contexto para o LLM."""
        context_parts = []
        context_parts.append(f"Intenção detectada da pergunta: {intencao}")

        # Histórico Blindado: Apenas as últimas perguntas do usuário para evitar envenenamento (alucinação)
        mensagens_usuario = [m for m in ultimas_mensagens if m.tipo_remetente == TipoRemetente.USUARIO]
        if mensagens_usuario:
            hist_str = "=== [HISTÓRICO RECENTE DE PERGUNTAS DO USUÁRIO] ===\n"
            for m in mensagens_usuario[-3:]: # Mantém apenas as 3 últimas perguntas
                hist_str += f"Usuário perguntou: {m.conteudo}\n"
            context_parts.append(hist_str)

        docs_str = "=== [BASE DE CONHECIMENTO] ===\n"
        if chunks_relevantes:
            for i, chunk in enumerate(chunks_relevantes, 1):
                docs_str += f"--- Documento {i} (Fonte: {chunk.fonte}) ---\n{chunk.conteudo}\n\n"
        else:
            docs_str += "Nenhuma informação relevante encontrada na base de dados para esta pergunta.\n"

        context_parts.append(docs_str)
        return "\n\n".join(context_parts)

    async def processar_pergunta(self, conversa_id: UUID, texto_usuario: str) -> ChatResult:
        if not texto_usuario or not texto_usuario.strip():
            raise ValueError("A pergunta não pode estar vazia.")

        # 1. Salva a mensagem do usuário
        msg_usuario = Mensagem(
            conversa_id=conversa_id,
            conteudo=texto_usuario.strip(),
            tipo_remetente=TipoRemetente.USUARIO,
            status_validacao=StatusValidacao.VALIDA,
        )
        msg_usuario = await self._conversa_repo.add_mensagem(msg_usuario)

        # 2. Recupera o histórico
        todas_mensagens = await self._conversa_repo.get_mensagens(conversa_id)
        historico_passado = [m for m in todas_mensagens if m.id != msg_usuario.id]

        # 3. Processamento de Linguagem Natural (NLP)
        nlp_result = await self._nlp.process(msg_usuario.conteudo)

        intencao = nlp_result.intencao
        query_busca = msg_usuario.conteudo.strip()

        print(f"\n{'=' * 50}")
        print(f"[DEBUG NLP] Intenção detectada: {intencao}")
        print(f"[DEBUG RAG] Query Vetorial: {query_busca}")

        # 4. ROTEAMENTO SEMÂNTICO
        if intencao == "SAUDACAO_OU_OUTROS":
            llm_response = await self._llm.generate(
                prompt=msg_usuario.conteudo,
                context="Intenção: SAUDACAO_OU_OUTROS. Aja como o CatBot, cumprimente o usuário e pergunte como pode ajudar com as normativas do IFES."
            )

        else:
            # Mapeia a intenção para a categoria salva no banco
            categoria_filtro = None
            if intencao == "DUVIDA_ROD":
                categoria_filtro = "ROD"
            elif intencao == "DUVIDA_PORTARIA":
                categoria_filtro = "PORTARIA"
            elif intencao == "DUVIDA_RESOLUCAO":
                categoria_filtro = "RESOLUCAO"

            print(f"[DEBUG RAG] Buscando apenas na Categoria: {categoria_filtro}")

            # Busca no banco vetorial passando a categoria
            chunks_relevantes = await self._kb.buscar_similar(
                query=query_busca,
                categoria=categoria_filtro,
                top_k=self._rag_top_k
            )

            print(f"[DEBUG RAG] Encontrou {len(chunks_relevantes)} pedaços de texto.")

            context = self._montar_contexto(chunks_relevantes, historico_passado, intencao)

            print(f"\n[DEBUG LLM] === CONTEXTO ENVIADO PARA A IA LER ===\n{context}\n{'=' * 50}\n")

            # Customiza o prompt dependendo da intenção para maior precisão
            prompt_final = f"Com base na [BASE DE CONHECIMENTO], responda: {msg_usuario.conteudo}"
            if categoria_filtro == "ROD":
                prompt_final = f"Com base nas normativas estudantis do ROD na [BASE DE CONHECIMENTO], responda: {msg_usuario.conteudo}"

            llm_response = await self._llm.generate(
                prompt=prompt_final,
                context=context,
            )

        # 5. Salva e retorna a resposta gerada
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