from abc import ABC, abstractmethod
from uuid import UUID
from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem
from catbot.domain.entities.resposta import Resposta, FonteResposta  # Adicione esta importação

class ConversaRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversa_id: UUID) -> Conversa | None: ...

    @abstractmethod
    async def save(self, conversa: Conversa) -> Conversa: ...

    @abstractmethod
    async def list_by_usuario(self, usuario_id: UUID) -> list[Conversa]: ...

    @abstractmethod
    async def add_mensagem(self, mensagem: Mensagem) -> Mensagem: ...

    @abstractmethod
    async def get_mensagens(self, conversa_id: UUID) -> list[Mensagem]: ...

    @abstractmethod # Novo método necessário para o fluxo de Chat
    async def save_resposta(self, resposta: Resposta) -> Resposta: ...

    @abstractmethod
    async def add_fonte_resposta(self, fonte: FonteResposta) -> FonteResposta:
        """Salva a origem (fonte) de uma resposta do bot."""
        pass

    @abstractmethod
    async def get_fontes_por_mensagem(self, mensagem_id: UUID) -> list[FonteResposta]:
        """Recupera as fontes utilizadas pelo bot para gerar uma resposta específica."""
        pass

    @abstractmethod
    async def list_all(self) -> list[Conversa]:
        """Retorna todas as conversas do banco (Necessário para o MetricsService)."""
        pass