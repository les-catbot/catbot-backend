from fastapi import APIRouter

from catbot.adapters.inbound.api.routes import chat, health, usuario, auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(usuario.router)
api_router.include_router(usuario.perfis_router)
api_router.include_router(auth.router)