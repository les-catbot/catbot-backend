from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Avaliacao:
    mensagem_id: UUID
    usuario_id: UUID
    nota: int
    comentario: str = ""
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
