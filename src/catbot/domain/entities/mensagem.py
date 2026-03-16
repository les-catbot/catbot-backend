from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


class TipoRemetente(StrEnum):
    USUARIO = "usuario"
    BOT = "bot"


class StatusValidacao(StrEnum):
    PENDENTE = "pendente"
    VALIDA = "valida"
    INVALIDA = "invalida"


@dataclass
class Mensagem:
    conversa_id: UUID
    conteudo: str
    tipo_remetente: TipoRemetente
    status_validacao: StatusValidacao = StatusValidacao.PENDENTE
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
