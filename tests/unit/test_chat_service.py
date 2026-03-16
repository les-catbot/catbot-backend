import pytest
from uuid import uuid4

from catbot.adapters.outbound.llm.stub_client import StubLLMClient
from catbot.adapters.outbound.nlp.stub_processor import StubNLPProcessor
from catbot.adapters.outbound.persistence.in_memory import InMemoryConversaRepository
from catbot.application.services.chat_service import ChatService
from catbot.domain.entities.conversa import Conversa


@pytest.fixture
def conversa_repo() -> InMemoryConversaRepository:
    return InMemoryConversaRepository()


@pytest.fixture
def chat_service(conversa_repo: InMemoryConversaRepository) -> ChatService:
    return ChatService(
        conversa_repo=conversa_repo,
        nlp_processor=StubNLPProcessor(),
        llm_client=StubLLMClient(),
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
