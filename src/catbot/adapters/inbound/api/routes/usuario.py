from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from catbot.adapters.inbound.api.dependencies import get_user_service, get_perfil_repository
from catbot.adapters.inbound.api.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, PerfilResponse
from catbot.application.services.user_service import UserService
from catbot.domain.ports.perfil_repository import PerfilRepository

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários - endpoints necessário para a gestão de usuários"]
)


@router.post(
    "/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar um novo usuário",
    description="""
    Cria um novo usuário no sistema vinculando-o a um **Perfil** existente.

    **Regras de negócio:**
    * O campo `email` deve ser único. Retorna erro `409` se já existir.
    * O `perfil_id` enviado deve existir previamente no banco de dados.
    * A senha enviada em texto plano será automaticamente convertida em hash no banco.
    """,
    response_description="Retorna os dados do usuário recém-criado (a senha é ocultada por segurança)."
)
async def criar_usuario(body: UsuarioCreate, service: UserService = Depends(get_user_service)):
    try:
        usuario_criado = await service.criar(body.model_dump())
        return usuario_criado
    except ValueError as e:
        if "já cadastrado" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/",
    response_model=list[UsuarioResponse],
    summary="Listar todos os usuários",
    description="Retorna uma lista contendo todos os usuários cadastrados no sistema. Útil para a tabela de listagem na tela de 'Gerenciar Usuários'.",
    response_description="Uma lista de objetos de usuários."
)
async def listar_usuarios(service: UserService = Depends(get_user_service)):
    return await service.listar()


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Obter detalhes de um usuário",
    description="Busca um usuário específico pelo seu UUID. Retorna erro `404` caso o ID não exista."
)
async def obter_usuario(usuario_id: UUID, service: UserService = Depends(get_user_service)):
    try:
        return await service.obter(usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Editar um usuário existente",
    description="""
    Atualiza os dados de um usuário específico.

    **Nota para o Front-end:** * Todos os campos no JSON de envio são opcionais. Envie apenas o que deseja alterar.
    * Se enviar uma nova `senha`, o hash antigo será sobrescrito. Se a senha não for alterada, não envie este campo.
    """
)
async def editar_usuario(usuario_id: UUID, body: UsuarioUpdate, service: UserService = Depends(get_user_service)):
    try:
        return await service.editar(usuario_id, body.model_dump(exclude_unset=True))
    except ValueError as e:
        if "já cadastrado" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um usuário",
    description="Remove permanentemente um usuário do banco de dados pelo seu ID."
)
async def eliminar_usuario(usuario_id: UUID, service: UserService = Depends(get_user_service)):
    try:
        await service.eliminar(usuario_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


perfis_router = APIRouter(
    prefix="/perfis",
    tags=["Perfis - Permissões de Acesso"]
)


@perfis_router.get(
    "/",
    response_model=list[PerfilResponse],
    summary="Listar perfis disponíveis",
    description="Retorna todos os perfis cadastrados no banco (Ex: Administrador, Usuário Padrão). **Use esta rota para preencher o dropdown de seleção na tela de cadastro de usuário.**"
)
async def listar_perfis(repo: PerfilRepository = Depends(get_perfil_repository)):
    return await repo.list_all()