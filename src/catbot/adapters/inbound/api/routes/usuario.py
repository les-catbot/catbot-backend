from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from catbot.adapters.inbound.api.dependencies import get_user_service
from catbot.adapters.inbound.api.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from catbot.application.services.user_service import UserService

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(body: UsuarioCreate, service: UserService = Depends(get_user_service)):
    try:
        return await service.criar(body.nome, body.email, body.senha)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[UsuarioResponse])
async def listar_usuarios(service: UserService = Depends(get_user_service)):
    return await service.listar()

@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(usuario_id: UUID, service: UserService = Depends(get_user_service)):
    try:
        return await service.obter(usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{usuario_id}", response_model=UsuarioResponse)
async def editar_usuario(usuario_id: UUID, body: UsuarioUpdate, service: UserService = Depends(get_user_service)):
    return await service.editar(usuario_id, body.nome, body.email)

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(usuario_id: UUID, service: UserService = Depends(get_user_service)):
    await service.eliminar(usuario_id)