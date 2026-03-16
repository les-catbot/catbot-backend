from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Resposta:
    mensagem_id: UUID
    texto_resposta: str
    pontuacao_confianca: float = 0.0
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FonteResposta:
    resposta_id: UUID
    documento_id: UUID
    trecho: str
    id: UUID = field(default_factory=uuid4)
