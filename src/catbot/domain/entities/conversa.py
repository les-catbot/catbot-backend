from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class Conversa:
    usuario_id: UUID
    status_sucesso: bool = False
    id: UUID = field(default_factory=uuid4)
    iniciado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    encerrado_em: datetime | None = None

    @property
    def esta_encerrada(self) -> bool:
        return self.encerrado_em is not None

    def encerrar(self, momento: datetime | None = None) -> None:
        """Marca a conversa como encerrada no instante informado (ou agora, em UTC)."""
        if self.encerrado_em is None:
            self.encerrado_em = momento or datetime.now(timezone.utc)
