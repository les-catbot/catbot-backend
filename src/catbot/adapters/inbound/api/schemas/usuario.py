from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class PerfilResponse(BaseModel):
    id: UUID
    nome: str
    descricao: str

    class Config:
        from_attributes = True

# --- SCHEMAS DE USUÁRIO ---
class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2)
    email: EmailStr
    senha: str = Field(..., min_length=6)
    perfil_id: UUID

class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: EmailStr | None = None
    senha: str | None = Field(None, min_length=6)
    perfil_id: UUID | None = None

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    perfil_id: UUID
    criado_em: datetime
    # O perfil aninhado é opcional, útil para quando a listagem fizer o JOIN
    perfil: PerfilResponse | None = None

    class Config:
        from_attributes = True