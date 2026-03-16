"""Dependency injection -- conecta ports com adapters concretos.

O container é montado uma vez no startup da aplicação.
As rotas recebem os serviços via Depends() do FastAPI.
"""

from catbot.adapters.outbound.llm.stub_client import StubLLMClient
from catbot.adapters.outbound.nlp.stub_processor import StubNLPProcessor
from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryAvaliacaoRepository,
    InMemoryConversaRepository,
    InMemoryDocumentoRepository,
    InMemoryUsuarioRepository,
)
from catbot.application.services.chat_service import ChatService
from catbot.application.services.evaluation_service import EvaluationService
from catbot.application.services.history_service import HistoryService
from catbot.application.services.knowledge_base_service import KnowledgeBaseService
from catbot.config import get_settings


class Container:
    """Poor-man's DI container. Troca fácil entre in-memory e SQLAlchemy."""

    def __init__(self) -> None:
        settings = get_settings()

        if settings.REPOSITORY_TYPE == "memory":
            self.usuario_repo = InMemoryUsuarioRepository()
            self.conversa_repo = InMemoryConversaRepository()
            self.documento_repo = InMemoryDocumentoRepository()
            self.avaliacao_repo = InMemoryAvaliacaoRepository()
        else:
            # TODO: instanciar repositórios SQLAlchemy quando implementados
            raise NotImplementedError(
                f"Repository type '{settings.REPOSITORY_TYPE}' ainda não implementado."
            )

        self.nlp_processor = StubNLPProcessor()
        self.llm_client = StubLLMClient()

        self.chat_service = ChatService(
            conversa_repo=self.conversa_repo,
            nlp_processor=self.nlp_processor,
            llm_client=self.llm_client,
        )
        self.knowledge_base_service = KnowledgeBaseService(
            documento_repo=self.documento_repo,
        )
        self.history_service = HistoryService(
            conversa_repo=self.conversa_repo,
        )
        self.evaluation_service = EvaluationService(
            avaliacao_repo=self.avaliacao_repo,
        )


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container()
    return _container


def get_chat_service() -> ChatService:
    return get_container().chat_service


def get_knowledge_base_service() -> KnowledgeBaseService:
    return get_container().knowledge_base_service


def get_history_service() -> HistoryService:
    return get_container().history_service


def get_evaluation_service() -> EvaluationService:
    return get_container().evaluation_service
