from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    titulo: str
    categoria: str
    fonte: str
    criado_em: datetime


class VersaoDocumentoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    documento_id: UUID
    numero_versao: int
    conteudo: str
    criado_em: datetime


class DocumentoDetalheResponse(DocumentoResponse):
    total_chunks: int
    versoes: list[VersaoDocumentoResponse]


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    documento_id: UUID
    conteudo: str
    indice_chunk: int
    categoria: str
    fonte: str
    pontuacao: float | None = None


class IndexacaoResponse(BaseModel):
    mensagem: str
    documento: DocumentoResponse
    total_chunks: int


class BuscaSemanticaRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
