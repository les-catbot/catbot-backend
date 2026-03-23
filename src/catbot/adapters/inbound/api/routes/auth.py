from fastapi import APIRouter, Depends, HTTPException, status
from catbot.adapters.inbound.api.dependencies import get_auth_service
from catbot.application.services.auth_service import AuthService
from catbot.adapters.inbound.api.schemas.auth import Token, LoginRequest

# Melhorando o nome da tag para ficar mais claro no Swagger
router = APIRouter(tags=["Autenticação - Login e Geração de Tokens"])


@router.post(
    "/login",
    response_model=Token,
    summary="Autenticar usuário (Login)",
    description="""
    Realiza a validação das credenciais do usuário e devolve um token de acesso.

    **Guia de Integração para o Front-end:**
    1. Envie o e-mail e a senha no corpo (Body) da requisição no formato **JSON**.
    2. Se as credenciais estiverem corretas, você receberá um `access_token` (JWT).
    3. Armazene este token (ex: no `localStorage` ou `sessionStorage`).
    4. Nas próximas requisições para rotas protegidas, insira o token no cabeçalho (Header) da seguinte forma:
       * `Authorization: Bearer <seu_token_aqui>`

    **Tratamento de Erros:**
    * Retorna `401 Unauthorized` caso o e-mail não exista ou a senha não bata.
    """,
    response_description="Objeto JSON contendo o token JWT gerado e o tipo do token."
)
async def login(
        body: LoginRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    token = await auth_service.autenticar(email=body.email, senha=body.senha)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )

    return Token(access_token=token, token_type="bearer")