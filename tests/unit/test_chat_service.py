from uuid import uuid4

import pytest

from catbot.adapters.outbound.embedding.stub_embedding import StubEmbeddingService
from catbot.adapters.outbound.llm.stub_client import StubLLMClient
from catbot.adapters.outbound.nlp.stub_processor import StubNLPProcessor
from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryConversaRepository,
    InMemoryDocumentoRepository,
    InMemoryVectorRepository,
)
from catbot.application.services.chat_service import ChatService
from catbot.application.services.knowledge_base_service import KnowledgeBaseService
from catbot.domain.entities.conversa import Conversa
from catbot.domain.ports.llm_client import LLMClient, LLMResponse


@pytest.fixture
def conversa_repo() -> InMemoryConversaRepository:
    return InMemoryConversaRepository()


@pytest.fixture
def chat_service(conversa_repo: InMemoryConversaRepository) -> ChatService:
    kb_service = KnowledgeBaseService(
        documento_repo=InMemoryDocumentoRepository(),
        embedding_service=StubEmbeddingService(),
        vector_repo=InMemoryVectorRepository(),
    )
    return ChatService(
        conversa_repo=conversa_repo,
        nlp_processor=StubNLPProcessor(),
        llm_client=StubLLMClient(),
        kb_service=kb_service,
    )


@pytest.mark.asyncio
async def test_processar_pergunta_retorna_resposta(
    conversa_repo: InMemoryConversaRepository,
    chat_service: ChatService,
):
    conversa = Conversa(usuario_id=uuid4())
    await conversa_repo.save(conversa)

    result = await chat_service.processar_pergunta(
        conversa_id=conversa.id,
        texto_usuario="O que é o IFES?",
    )

    assert result.resposta
    assert result.confianca >= 0
    assert result.mensagem_id is not None


@pytest.mark.asyncio
async def test_processar_pergunta_vazia_levanta_erro(chat_service: ChatService):
    with pytest.raises(ValueError, match="vazia"):
        await chat_service.processar_pergunta(
            conversa_id=uuid4(),
            texto_usuario="",
        )


@pytest.mark.asyncio
async def test_saudacao_nao_usa_contexto_rag(conversa_repo: InMemoryConversaRepository):
    class RecordingLLM(LLMClient):
        def __init__(self) -> None:
            self.calls = []

        async def generate(
            self,
            prompt: str,
            context: str = "",
            system_prompt_override: str | None = None,
        ) -> LLMResponse:
            self.calls.append(
                {
                    "prompt": prompt,
                    "context": context,
                    "system_prompt_override": system_prompt_override,
                }
            )
            return LLMResponse(texto="Olá! Como posso ajudar?", confianca=0.9)

    llm = RecordingLLM()
    kb_service = KnowledgeBaseService(
        documento_repo=InMemoryDocumentoRepository(),
        embedding_service=StubEmbeddingService(),
        vector_repo=InMemoryVectorRepository(),
    )
    service = ChatService(
        conversa_repo=conversa_repo,
        nlp_processor=StubNLPProcessor(intencao="SAUDACAO_OU_OUTROS"),
        llm_client=llm,
        kb_service=kb_service,
    )
    conversa = await conversa_repo.save(Conversa(usuario_id=uuid4()))

    await service.processar_pergunta(conversa.id, "Oi")

    assert llm.calls[0]["context"] == ""
    assert llm.calls[0]["system_prompt_override"] is not None
