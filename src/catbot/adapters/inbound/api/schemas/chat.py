from uuid import UUID
from typing import List
from pydantic import BaseModel, Field

# --- Schemas para Iniciar Conversa ---
class NovaConversaRequest(BaseModel):
    usuario_id: UUID

class NovaConversaResponse(BaseModel):
    conversa_id: UUID

# --- Schemas de Fontes (Rastreabilidade) ---
class FonteResponse(BaseModel):
    documento_id: UUID
    trecho: str

# --- Schemas para Perguntas e Respostas ---
class PerguntaRequest(BaseModel):
    conversa_id: UUID
    texto: str

class PerguntaResponse(BaseModel):
    resposta: str
    confianca: float
    mensagem_id: UUID
    fontes: List[FonteResponse] = Field(default_factory=list)