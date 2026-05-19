from fastapi import APIRouter

from catbot.adapters.inbound.api.routes import auth, avaliacao, chat, documento, health, historico, usuario, exportacao, \
    metricas

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(usuario.router)
api_router.include_router(documento.router)
api_router.include_router(historico.router)
api_router.include_router(usuario.perfis_router)
api_router.include_router(auth.router)
api_router.include_router(avaliacao.router)
api_router.include_router(exportacao.router)
api_router.include_router(metricas.router)