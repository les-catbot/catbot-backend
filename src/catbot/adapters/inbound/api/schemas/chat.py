from uuid import UUID
from pydantic import BaseModel, Field

# --- Novos Schemas para Iniciar Conversa ---
class NovaConversaRequest(BaseModel):
    usuario_id: UUID

class NovaConversaResponse(BaseModel):
    conversa_id: UUID

# --- Schemas Existentes ---
class PerguntaRequest(BaseModel):
    conversa_id: UUID
    texto: str = Field(..., min_length=1, max_length=2000)

class PerguntaResponse(BaseModel):
    resposta: str
    confianca: float
    mensagem_id: UUID
    fontes: list[FonteResponse] = []


class FonteResponse(BaseModel):
    documento_id: UUID # Ou string, dependendo de como você mapeia o chunk.fonte
    trecho: str