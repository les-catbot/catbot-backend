from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Intencao:
    nome: str
    descricao: str = ""
    id: UUID = field(default_factory=uuid4)
