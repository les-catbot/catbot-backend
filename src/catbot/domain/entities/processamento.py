from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class ProcessamentoPergunta:
    mensagem_id: UUID
    texto_normalizado: str
    tokens: str
    intencao_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EntidadeExtraida:
    processamento_id: UUID
    nome_entidade: str
    valor_entidade: str
    id: UUID = field(default_factory=uuid4)
