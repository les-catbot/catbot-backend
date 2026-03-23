from fastapi import APIRouter, Depends, HTTPException, status
from catbot.adapters.inbound.api.dependencies import get_auth_service
from catbot.application.services.auth_service import AuthService
from catbot.adapters.inbound.api.schemas.auth import Token, LoginRequest

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
        body: LoginRequest,  # <-- O FastAPI entende automaticamente que isso é um JSON no Body
        auth_service: AuthService = Depends(get_auth_service)
):
    # Passamos os dados que vieram do JSON
    token = await auth_service.autenticar(email=body.email, senha=body.senha)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )

    return Token(access_token=token, token_type="bearer")