from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from catbot.adapters.inbound.api.dependencies import get_user_service, get_perfil_repository
from catbot.adapters.inbound.api.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, PerfilResponse
from catbot.application.services.user_service import UserService
from catbot.domain.ports.perfil_repository import PerfilRepository

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# 3. Rota de Criação
@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_usuario(body: UsuarioCreate, service: UserService = Depends(get_user_service)):
    try:
        # Passa os dados como dicionário para o serviço
        usuario_criado = await service.criar(body.model_dump())
        return usuario_criado
    except ValueError as e:
        # 409 Conflict para violação de unicidade (e-mail) ou 400 Bad Request
        if "já cadastrado" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# 4. Rota de Listagem
@router.get("/", response_model=list[UsuarioResponse])
async def listar_usuarios(service: UserService = Depends(get_user_service)):
    return await service.listar()

# Rota para obter usuário específico
@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obter_usuario(usuario_id: UUID, service: UserService = Depends(get_user_service)):
    try:
        return await service.obter(usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# 5. Rota de Edição
@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def editar_usuario(usuario_id: UUID, body: UsuarioUpdate, service: UserService = Depends(get_user_service)):
    try:
        return await service.editar(usuario_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        if "já cadastrado" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# 6. Rota de Exclusão
@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(usuario_id: UUID, service: UserService = Depends(get_user_service)):
    try:
        await service.eliminar(usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# --- 2. Rota de Perfis ---
# Idealmente ficaria em `routes/perfil.py`, mas para facilidade pode colocar aqui temporariamente ou criar um roteador próprio.
perfis_router = APIRouter(prefix="/perfis", tags=["perfis"])

@perfis_router.get("/perfil", response_model=list[PerfilResponse])
async def listar_perfis(repo: PerfilRepository = Depends(get_perfil_repository)):
    return await repo.list_all()