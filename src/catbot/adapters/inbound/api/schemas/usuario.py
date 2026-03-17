from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2)
    email: EmailStr
    senha: str = Field(..., min_length=6)

class UsuarioUpdate(BaseModel):
    nome: str | None = None
    email: EmailStr | None = None

class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: EmailStr
    criado_em: datetime

    class Config:
        from_attributes = True