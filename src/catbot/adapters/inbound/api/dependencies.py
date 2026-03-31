"""Dependency injection -- conecta ports com adapters concretos.

O container é montado uma vez no startup da aplicação.
As rotas recebem os serviços via Depends() do FastAPI.
"""
import uuid
from catbot.domain.entities.perfil import Perfil
from catbot.domain.ports.perfil_repository import PerfilRepository
from catbot.adapters.outbound.persistence.in_memory.perfil_repository import InMemoryPerfilRepository
# IMPORTAÇÃO NOVA: O repositório definitivo do SQLAlchemy
from catbot.adapters.outbound.persistence.sqlalchemy.repositories.perfil_repository import SQLAlchemyPerfilRepository

from catbot.adapters.outbound.embedding.ollama_embedding import OllamaEmbeddingService
from catbot.adapters.outbound.embedding.stub_embedding import StubEmbeddingService
from catbot.adapters.outbound.llm.stub_client import StubLLMClient
from catbot.adapters.outbound.nlp.stub_processor import StubNLPProcessor
from catbot.adapters.outbound.persistence.in_memory import (
    InMemoryAvaliacaoRepository,
    InMemoryConversaRepository,
    InMemoryDocumentoRepository,
    InMemoryUsuarioRepository,
    InMemoryVectorRepository,
)
from catbot.adapters.outbound.persistence.sqlalchemy.database import (
    create_session_factory,
)
from catbot.adapters.outbound.persistence.sqlalchemy.repositories import (
    SQLAlchemyAvaliacaoRepository,
    SQLAlchemyConversaRepository,
    SQLAlchemyDocumentoRepository,
    SQLAlchemyUsuarioRepository,
    SQLAlchemyVectorRepository,
)
from catbot.application.services.chat_service import ChatService
from catbot.application.services.evaluation_service import EvaluationService
from catbot.application.services.history_service import HistoryService
from catbot.application.services.knowledge_base_service import KnowledgeBaseService
from catbot.application.services.user_service import UserService
from catbot.config import get_settings
from catbot.application.services.auth_service import AuthService

class Container:
    """Poor-man's DI container. Troca fácil entre in-memory e SQLAlchemy."""

    def __init__(self) -> None:
        settings = get_settings()

        if settings.REPOSITORY_TYPE == "memory":
            self.perfil_repo = InMemoryPerfilRepository()

            perfil_admin = Perfil(id=uuid.UUID("00000000-0000-0000-0000-000000000001"), nome="Administrador", descricao="Acesso total ao sistema")
            perfil_user = Perfil(id=uuid.UUID("00000000-0000-0000-0000-000000000002"), nome="Usuário Padrão", descricao="Acesso comum")
            self.perfil_repo._store[perfil_admin.id] = perfil_admin
            self.perfil_repo._store[perfil_user.id] = perfil_user

            self.usuario_repo = InMemoryUsuarioRepository()
            self.conversa_repo = InMemoryConversaRepository()
            self.documento_repo = InMemoryDocumentoRepository()
            self.avaliacao_repo = InMemoryAvaliacaoRepository()
            self.vector_repo = InMemoryVectorRepository()

        elif settings.REPOSITORY_TYPE == "sqlalchemy":
            sf = create_session_factory(
                settings.DATABASE_URL, echo=settings.DATABASE_ECHO
            )

            # SOLUÇÃO DEFINITIVA: Injetando o repositório conectado ao banco de dados real
            self.perfil_repo = SQLAlchemyPerfilRepository(sf)

            self.usuario_repo = SQLAlchemyUsuarioRepository(sf)
            self.conversa_repo = SQLAlchemyConversaRepository(sf)
            self.documento_repo = SQLAlchemyDocumentoRepository(sf)
            self.avaliacao_repo = SQLAlchemyAvaliacaoRepository(sf)
            self.vector_repo = SQLAlchemyVectorRepository(sf)
        else:
            raise NotImplementedError(
                f"Repository type '{settings.REPOSITORY_TYPE}' não suportado."
            )

        if settings.EMBEDDING_TYPE == "ollama":
            self.embedding_service = OllamaEmbeddingService(
                base_url=settings.LLM_BASE_URL,
                model=settings.EMBEDDING_MODEL,
            )
        else:
            self.embedding_service = StubEmbeddingService()

        self.nlp_processor = StubNLPProcessor()
        self.llm_client = StubLLMClient()

        self.chat_service = ChatService(
            conversa_repo=self.conversa_repo,
            nlp_processor=self.nlp_processor,
            llm_client=self.llm_client,
        )
        self.knowledge_base_service = KnowledgeBaseService(
            documento_repo=self.documento_repo,
            embedding_service=self.embedding_service,
            vector_repo=self.vector_repo,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        self.history_service = HistoryService(
            conversa_repo=self.conversa_repo,
        )
        self.evaluation_service = EvaluationService(
            avaliacao_repo=self.avaliacao_repo,
        )

        self.user_service = UserService(
            usuario_repo=self.usuario_repo,
            perfil_repo=self.perfil_repo,
        )
        self.auth_service = AuthService(
            usuario_repo=self.usuario_repo
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