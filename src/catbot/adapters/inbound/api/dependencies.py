"""Dependency injection -- conecta ports com adapters concretos.

O container é montado uma vez no startup da aplicação.
As rotas recebem os serviços via Depends() do FastAPI.
"""
import uuid
from catbot.domain.entities.perfil import Perfil
from catbot.domain.ports.perfil_repository import PerfilRepository
from catbot.adapters.outbound.persistence.in_memory.perfil_repository import InMemoryPerfilRepository

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
from catbot.application.services.user_service import UserService
from catbot.config import get_settings


class Container:
    """Poor-man's DI container. Troca fácil entre in-memory e SQLAlchemy."""

    def __init__(self) -> None:
        settings = get_settings()

        if settings.REPOSITORY_TYPE == "memory":
            self.perfil_repo = InMemoryPerfilRepository()

            # --- MOCK / SEEDS PARA O BANCO EM MEMÓRIA ---
            # Isso simula os perfis que já estariam salvos no banco de dados real
            perfil_admin = Perfil(id=uuid.UUID("00000000-0000-0000-0000-000000000001"), nome="Administrador", descricao="Acesso total ao sistema")
            perfil_user = Perfil(id=uuid.UUID("00000000-0000-0000-0000-000000000002"), nome="Usuário Padrão", descricao="Acesso comum")
            self.perfil_repo._store[perfil_admin.id] = perfil_admin
            self.perfil_repo._store[perfil_user.id] = perfil_user
            # ---------------------------------------------

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

        # Instanciação dos serviços
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
        # Adição do UserService ao container (agora injetando o perfil_repo também)
        self.user_service = UserService(
            usuario_repo=self.usuario_repo,
            perfil_repo=self.perfil_repo,
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