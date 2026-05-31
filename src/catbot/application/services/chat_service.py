"""Caso de uso: Realizar Pergunta em Linguagem Natural com Histórico (Memória)."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from catbot.application.services.knowledge_base_service import KnowledgeBaseService
from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem, StatusValidacao, TipoRemetente
from catbot.domain.entities.processamento import EntidadeExtraida, ProcessamentoPergunta
from catbot.domain.entities.resposta import FonteResposta, Resposta
from catbot.domain.ports.conversa_repository import ConversaRepository
from catbot.domain.ports.llm_client import LLMClient
from catbot.domain.ports.nlp_processor import NLPProcessor


@dataclass
class ChatResult:
    resposta: str
    confianca: float
    mensagem_id: UUID
    fontes: list[FonteResposta] = field(default_factory=list)


def _to_utc(momento: datetime) -> datetime:
    """Garante comparação segura tratando datas sem fuso como UTC."""
    if momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


class ChatService:
    def __init__(
        self,
        conversa_repo: ConversaRepository,
        nlp_processor: NLPProcessor,
        llm_client: LLMClient,
        kb_service: KnowledgeBaseService,
        rag_top_k: int = 3,
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

    async def encerrar_conversa(
        self, conversa_id: UUID, momento: datetime | None = None
    ) -> Conversa:
        """Encerra manualmente uma conversa. Idempotente: reencerrar não altera o timestamp."""
        conversa = await self._conversa_repo.get_by_id(conversa_id)
        if conversa is None:
            raise LookupError("Conversa não encontrada.")
        if conversa.esta_encerrada:
            return conversa

        encerrado_em = momento or datetime.now(timezone.utc)
        encerrada = await self._conversa_repo.encerrar(conversa_id, encerrado_em)
        return encerrada or conversa

    async def encerrar_inativas(
        self, timeout_minutos: int, agora: datetime | None = None
    ) -> list[UUID]:
        """Encerra conversas sem novas mensagens há mais de `timeout_minutos`.

        A inatividade é medida pela última mensagem da conversa (ou pelo
        `iniciado_em`, caso ainda não haja mensagens). Retorna os ids encerrados.
        """
        agora = agora or datetime.now(timezone.utc)
        limite = agora - timedelta(minutes=timeout_minutos)

        encerradas: list[UUID] = []
        for conversa in await self._conversa_repo.list_abertas():
            ultima_atividade = await self._ultima_atividade(conversa)
            if ultima_atividade <= limite:
                await self._conversa_repo.encerrar(conversa.id, agora)
                encerradas.append(conversa.id)
        return encerradas

    async def _ultima_atividade(self, conversa: Conversa) -> datetime:
        mensagens = await self._conversa_repo.get_mensagens(conversa.id)
        if not mensagens:
            return _to_utc(conversa.iniciado_em)
        return max(_to_utc(m.criado_em) for m in mensagens)

    def _montar_contexto(
        self,
        chunks_relevantes: list,
        ultimas_mensagens: list,
        intencao: str,
    ) -> str:
        """Organiza visualmente o contexto para o LLM ler."""
        context_parts = [f"Intenção detectada da pergunta: {intencao}"]

        # Histórico Blindado
        mensagens_usuario = [
            m for m in ultimas_mensagens if m.tipo_remetente == TipoRemetente.USUARIO
        ]
        if mensagens_usuario:
            hist_str = "=== [HISTÓRICO RECENTE DE PERGUNTAS DO USUÁRIO] ===\n"
            for m in mensagens_usuario[-3:]:
                hist_str += f"Usuário perguntou: {m.conteudo}\n"
            context_parts.append(hist_str)

        docs_str = "=== [BASE DE CONHECIMENTO] ===\n"
        if chunks_relevantes:
            for i, chunk in enumerate(chunks_relevantes, 1):
                docs_str += f"--- Documento {i} (Fonte: {chunk.fonte}) ---\n{chunk.conteudo}\n\n"
        else:
            docs_str += (
                "Nenhuma informação relevante encontrada na base de dados para esta "
                "pergunta.\n"
            )

        context_parts.append(docs_str)
        return "\n\n".join(context_parts)

    async def processar_pergunta(self, conversa_id: UUID, texto_usuario: str) -> ChatResult:
        if not texto_usuario or not texto_usuario.strip():
            raise ValueError("A pergunta não pode estar vazia.")

        conversa = await self._conversa_repo.get_by_id(conversa_id)
        if conversa is None:
            raise LookupError("Conversa não encontrada.")
        if conversa.esta_encerrada:
            raise ValueError("Conversa encerrada. Inicie uma nova conversa para continuar.")

        msg_usuario = Mensagem(
            conversa_id=conversa_id,
            conteudo=texto_usuario.strip(),
            tipo_remetente=TipoRemetente.USUARIO,
            status_validacao=StatusValidacao.VALIDA,
        )
        msg_usuario = await self._conversa_repo.add_mensagem(msg_usuario)

        todas_mensagens = await self._conversa_repo.get_mensagens(conversa_id)
        historico_passado = [m for m in todas_mensagens if m.id != msg_usuario.id]

        nlp_result = await self._nlp.process(msg_usuario.conteudo)
        processamento = ProcessamentoPergunta(
            mensagem_id=msg_usuario.id,
            texto_normalizado=nlp_result.texto_normalizado,
            tokens=json.dumps(nlp_result.tokens, ensure_ascii=True),
        )
        entidades_extraidas = [
            EntidadeExtraida(
                processamento_id=processamento.id,
                nome_entidade=nome,
                valor_entidade=str(valor),
            )
            for nome, valor in nlp_result.entidades.items()
        ]
        await self._conversa_repo.save_processamento(
            processamento=processamento,
            entidades=entidades_extraidas,
            intencao_nome=nlp_result.intencao,
        )

        intencao = nlp_result.intencao
        query_busca = msg_usuario.conteudo.strip()
        chunks_relevantes = []

        if intencao == "SAUDACAO_OU_OUTROS":
            llm_response = await self._llm.generate(
                prompt=msg_usuario.conteudo,
                system_prompt_override=(
                    "Você é o CatBot, o assistente virtual institucional do IFES "
                    "Campus Colatina. Cumprimente o usuário em português do Brasil "
                    "e ofereça ajuda sobre documentos institucionais."
                ),
            )
        else:
            categoria_filtro = {
                "DUVIDA_ROD": "ROD",
                "DUVIDA_PORTARIA": "PORTARIA",
                "DUVIDA_RESOLUCAO": "RESOLUCAO",
            }.get(intencao)

            chunks_relevantes = await self._kb.buscar_similar(
                query=query_busca,
                categoria=categoria_filtro,
                top_k=self._rag_top_k
            )
            context = self._montar_contexto(chunks_relevantes, historico_passado, intencao)

            llm_response = await self._llm.generate(prompt=msg_usuario.conteudo, context=context)

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

        fontes_salvas = []
        if chunks_relevantes:
            for chunk in chunks_relevantes:
                fonte = FonteResposta(
                    resposta_id=resposta.id,
                    documento_id=chunk.documento_id,
                    trecho=chunk.conteudo
                )
                if hasattr(self._conversa_repo, 'add_fonte_resposta'):
                    await self._conversa_repo.add_fonte_resposta(fonte)
                fontes_salvas.append(fonte)

        return ChatResult(
            resposta=llm_response.texto,
            confianca=llm_response.confianca,
            mensagem_id=msg_bot.id,
            fontes=fontes_salvas
        )
