from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem
from catbot.domain.entities.processamento import EntidadeExtraida, ProcessamentoPergunta
from catbot.domain.entities.resposta import FonteResposta, Resposta


class ConversaRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversa_id: UUID) -> Conversa | None: ...

    @abstractmethod
    async def save(self, conversa: Conversa) -> Conversa: ...

    @abstractmethod
    async def list_by_usuario(self, usuario_id: UUID) -> list[Conversa]: ...

    @abstractmethod
    async def encerrar(self, conversa_id: UUID, encerrado_em: datetime) -> Conversa | None:
        """Registra o instante de encerramento de uma conversa. Idempotente."""
        ...

    @abstractmethod
    async def list_abertas(self) -> list[Conversa]:
        """Lista conversas ainda não encerradas (encerrado_em IS NULL)."""
        ...

    @abstractmethod
    async def add_mensagem(self, mensagem: Mensagem) -> Mensagem: ...

    @abstractmethod
    async def get_mensagens(self, conversa_id: UUID) -> list[Mensagem]: ...

    @abstractmethod # Novo método necessário para o fluxo de Chat
    async def save_resposta(self, resposta: Resposta) -> Resposta: ...

    @abstractmethod
    async def save_processamento(
        self,
        processamento: ProcessamentoPergunta,
        entidades: list[EntidadeExtraida],
        intencao_nome: str | None = None,
    ) -> ProcessamentoPergunta:
        """Salva a versão processada internamente da pergunta e suas entidades."""
        ...

    @abstractmethod
    async def get_processamento_por_mensagem(
        self,
        mensagem_id: UUID,
    ) -> tuple[ProcessamentoPergunta | None, list[EntidadeExtraida]]:
        """Recupera o processamento e as entidades ligadas a uma mensagem."""
        ...

    @abstractmethod
    async def add_fonte_resposta(self, fonte: FonteResposta) -> FonteResposta:
        """Salva a origem (fonte) de uma resposta do bot."""
        ...

    @abstractmethod
    async def get_fontes_por_mensagem(self, mensagem_id: UUID) -> list[FonteResposta]:
        """Recupera as fontes utilizadas pelo bot para gerar uma resposta específica."""
        ...

    @abstractmethod
    async def list_all(self) -> list[Conversa]:
        """Retorna todas as conversas do banco (Necessário para o MetricsService)."""
        ...
