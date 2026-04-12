from abc import ABC, abstractmethod
from uuid import UUID
from catbot.domain.entities.conversa import Conversa
from catbot.domain.entities.mensagem import Mensagem
from catbot.domain.entities.resposta import Resposta # Adicione esta importação

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