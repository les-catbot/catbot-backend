from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# === MOVIDO PARA CIMA: O Python precisa ler isso primeiro ===
class FonteRespostaSchema(BaseModel):
    documento_id: UUID
    trecho: str


class MensagemResponse(BaseModel):
    id: UUID
    conversa_id: UUID
    conteudo: str
    tipo_remetente: str
    status_validacao: str
    criado_em: datetime
    fontes: Optional[list[FonteRespostaSchema]] = None


class ConversaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    usuario_id: UUID
    status_sucesso: bool
    iniciado_em: datetime
    encerrado_em: datetime | None = None


class ConversaDetalheResponse(BaseModel):
    conversa: ConversaResponse
    mensagens: list[MensagemResponse]


class FiltroPeridoRequest(BaseModel):
    inicio: datetime
    fim: datetime