import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from catbot.adapters.inbound.api.dependencies import get_container
from catbot.adapters.inbound.api.router import api_router
from catbot.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apenas inicializamos as injeções de dependência da Arquitetura Hexagonal.
    # As migrações do banco de dados (Alembic) devem ser rodadas separadamente
    # via CLI para evitar travamentos (deadlocks) no boot do servidor assíncrono.
    get_container()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="CatBot API",
        description="Backend do chatbot CatBot — arquitetura hexagonal",
        version="0.1.0",
        debug=settings.APP_DEBUG,
        lifespan=lifespan,
    )

    # Configuração de CORS para permitir que o frontend comunique com a API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Regista todas as rotas (Inbound Adapters)
    app.include_router(api_router)
    return app


app = create_app()