from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Documento:
    titulo: str
    categoria: str
    fonte: str
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VersaoDocumento:
    documento_id: UUID
    numero_versao: int
    conteudo: str
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
