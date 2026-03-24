from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

# Importe a entidade de Perfil (certifique-se de que o caminho está correto)
from catbot.domain.entities.perfil import Perfil

@dataclass
class Usuario:
    nome: str
    email: str
    senha_hash: str
    perfil_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)
    criado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Novo campo para armazenar o objeto do perfil e enviá-lo para o JSON de resposta
    perfil: Perfil | None = None