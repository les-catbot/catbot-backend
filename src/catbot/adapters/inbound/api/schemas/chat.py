from uuid import UUID

from pydantic import BaseModel, Field


class PerguntaRequest(BaseModel):
    conversa_id: UUID
    texto: str = Field(..., min_length=1, max_length=2000)


class PerguntaResponse(BaseModel):
    resposta: str
    confianca: float
    mensagem_id: UUID
