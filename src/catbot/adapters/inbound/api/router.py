from fastapi import APIRouter

from catbot.adapters.inbound.api.routes import chat, health, usuario

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(usuario.router) # Registe a rota
