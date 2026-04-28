from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AvaliacaoRequest(BaseModel):
    mensagem_id: UUID
    usuario_id: UUID
    nota: int = Field(..., ge=1, le=5)
    comentario: str = ""


class AvaliacaoResponse(BaseModel):
    id: UUID
    mensagem_id: UUID
    usuario_id: UUID
    nota: int
    comentario: str
    criado_em: datetime


class AvaliacaoListResponse(BaseModel):
    avaliacoes: list[AvaliacaoResponse]
    total: int
