"""Dependency injection -- conecta ports com adapters concretos."""

import uuid

from catbot.adapters.outbound.embedding.ollama_embedding import OllamaEmbeddingService
from catbot.adapters.outbound.embedding.openai_embedding import OpenAIEmbeddingService
from catbot.adapters.outbound.embedding.stub_embedding import StubEmbeddingService
from catbot.adapters.outbound.llm.ollama_client import OllamaLLMClient
from catbot.adapters.outbound.llm.openai_client import OpenAILLMClient
from catbot.adapters.outbound.llm.stub_client import StubLLMClient
from catbot.adapters.outbound.nlp.hybrid_nlp_processor import HybridNLPProcessor
from catbot.adapters.outbound.nlp.spacy_processor import SpacyNLPProcessor
from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryAvaliacaoRepository,
    InMemoryConversaRepository,
    InMemoryDocumentoRepository,
    InMemoryUsuarioRepository,
    InMemoryVectorRepository,
)
from catbot.adapters.outbound.persistence.in_memory.perfil_repository import (
    InMemoryPerfilRepository,
)
from catbot.adapters.outbound.persistence.sqlalchemy.database import create_session_factory
from catbot.adapters.outbound.persistence.sqlalchemy.repositories import (
    SQLAlchemyAvaliacaoRepository,
    SQLAlchemyConversaRepository,
    SQLAlchemyDocumentoRepository,
    SQLAlchemyUsuarioRepository,
    SQLAlchemyVectorRepository,
)
from catbot.adapters.outbound.persistence.sqlalchemy.repositories.perfil_repository import (
    SQLAlchemyPerfilRepository,
)
from catbot.application.services.auth_service import AuthService
from catbot.application.services.chat_service import ChatService
from catbot.application.services.evaluation_service import EvaluationService
from catbot.application.services.export_service import ExportService
from catbot.application.services.history_service import HistoryService
from catbot.application.services.knowledge_base_service import KnowledgeBaseService
from catbot.application.services.metrics_service import MetricsService
from catbot.application.services.user_service import UserService
from catbot.config import get_settings
from catbot.domain.entities.perfil import Perfil
from catbot.domain.ports.perfil_repository import PerfilRepository


class Container:
    """Poor-man's DI container for the hexagonal adapters."""

    def __init__(self) -> None:
        settings = get_settings()

        repository_type = settings.REPOSITORY_TYPE.lower()
        if repository_type == "memory":
            self._configure_memory_repositories()
        elif repository_type == "sqlalchemy":
            session_factory = create_session_factory(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
            )
            self.perfil_repo = SQLAlchemyPerfilRepository(session_factory)
            self.usuario_repo = SQLAlchemyUsuarioRepository(session_factory)
            self.conversa_repo = SQLAlchemyConversaRepository(session_factory)
            self.documento_repo = SQLAlchemyDocumentoRepository(session_factory)
            self.avaliacao_repo = SQLAlchemyAvaliacaoRepository(session_factory)
            self.vector_repo = SQLAlchemyVectorRepository(session_factory)
        else:
            raise NotImplementedError(
                f"Repository type '{settings.REPOSITORY_TYPE}' não suportado."
            )

        openai_api_key = settings.OPENAI_API_KEY.strip()
        self.embedding_service = self._build_embedding_service(settings, openai_api_key)
        self.llm_client = self._build_llm_client(settings, openai_api_key)

        self.spacy_processor = SpacyNLPProcessor()
        self.nlp_processor = HybridNLPProcessor(
            spacy_processor=self.spacy_processor,
            llm_client=self.llm_client,
        )

        self.knowledge_base_service = KnowledgeBaseService(
            documento_repo=self.documento_repo,
            embedding_service=self.embedding_service,
            vector_repo=self.vector_repo,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self.chat_service = ChatService(
            conversa_repo=self.conversa_repo,
            nlp_processor=self.nlp_processor,
            llm_client=self.llm_client,
            kb_service=self.knowledge_base_service,
            rag_top_k=settings.RAG_TOP_K,
        )
        self.history_service = HistoryService(conversa_repo=self.conversa_repo)
        self.evaluation_service = EvaluationService(avaliacao_repo=self.avaliacao_repo)
        self.user_service = UserService(
            usuario_repo=self.usuario_repo,
            perfil_repo=self.perfil_repo,
        )
        self.auth_service = AuthService(usuario_repo=self.usuario_repo)
        self.export_service = ExportService(
            conversa_repo=self.conversa_repo,
            history_service=self.history_service,
            documento_repo=self.documento_repo,
        )
        self.metrics_service = MetricsService(conversa_repo=self.conversa_repo)

    def _configure_memory_repositories(self) -> None:
        self.perfil_repo = InMemoryPerfilRepository()

        perfil_admin = Perfil(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            nome="Administrador",
            descricao="Acesso total ao sistema",
        )
        perfil_user = Perfil(
            id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
            nome="Usuário Padrão",
            descricao="Acesso comum",
        )
        self.perfil_repo._store[perfil_admin.id] = perfil_admin
        self.perfil_repo._store[perfil_user.id] = perfil_user

        self.usuario_repo = InMemoryUsuarioRepository()
        self.conversa_repo = InMemoryConversaRepository()
        self.documento_repo = InMemoryDocumentoRepository()
        self.avaliacao_repo = InMemoryAvaliacaoRepository()
        self.vector_repo = InMemoryVectorRepository()

    def _build_llm_client(self, settings, openai_api_key: str):
        provider = settings.LLM_PROVIDER.lower()
        if provider == "openai":
            if not openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY não configurada. Defina a chave no arquivo .env."
                )
            return OpenAILLMClient(api_key=openai_api_key, model=settings.LLM_MODEL)
        if provider == "ollama":
            return OllamaLLMClient(
                base_url=settings.LLM_BASE_URL,
                model=settings.LLM_MODEL,
            )
        if provider == "stub":
            return StubLLMClient()
        raise NotImplementedError(f"LLM provider '{settings.LLM_PROVIDER}' não suportado.")

    def _build_embedding_service(self, settings, openai_api_key: str):
        provider = (settings.EMBEDDING_PROVIDER or settings.EMBEDDING_TYPE).lower()
        if provider == "openai":
            if not openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY não configurada. Defina a chave no arquivo .env."
                )
            return OpenAIEmbeddingService(
                api_key=openai_api_key,
                model=settings.EMBEDDING_MODEL,
            )
        if provider == "ollama":
            return OllamaEmbeddingService(
                base_url=settings.LLM_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
        if provider == "stub":
            return StubEmbeddingService()
        raise NotImplementedError(
            f"Embedding provider '{settings.EMBEDDING_PROVIDER}' não suportado."
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


def get_user_service() -> UserService:
    return get_container().user_service


def get_perfil_repository() -> PerfilRepository:
    return get_container().perfil_repo


def get_auth_service() -> AuthService:
    return get_container().auth_service


def get_export_service() -> ExportService:
    return get_container().export_service


def get_metrics_service() -> MetricsService:
    return get_container().metrics_service
