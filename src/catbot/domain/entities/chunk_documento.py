from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class ChunkDocumento:
    documento_id: UUID
    versao_id: UUID
    conteudo: str
    indice_chunk: int
    embedding: list[float]
    categoria: str = ""
    fonte: str = ""
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
