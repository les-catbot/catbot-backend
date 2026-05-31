import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from catbot.adapters.inbound.api.dependencies import get_container
from catbot.adapters.inbound.api.router import api_router
from catbot.config import Settings, get_settings

logger = logging.getLogger(__name__)


async def _auto_encerrar_conversas_loop(container, settings: Settings) -> None:
    """Varre periodicamente as conversas abertas e encerra as inativas."""
    intervalo = max(1, settings.CONVERSA_TIMEOUT_CHECK_INTERVAL_SECONDS)
    timeout = settings.CONVERSA_TIMEOUT_MINUTES
    while True:
        try:
            await asyncio.sleep(intervalo)
            encerradas = await container.chat_service.encerrar_inativas(timeout)
            if encerradas:
                logger.info(
                    "Encerradas %d conversa(s) por inatividade (timeout=%dmin).",
                    len(encerradas),
                    timeout,
                )
        except asyncio.CancelledError:
            break
        except Exception:  # noqa: BLE001 - o loop não pode morrer por erro pontual
            logger.exception("Falha na varredura de encerramento automático de conversas.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apenas inicializamos as injeções de dependência da Arquitetura Hexagonal.
    # As migrações do banco de dados (Alembic) devem ser rodadas separadamente
    # via CLI para evitar travamentos (deadlocks) no boot do servidor assíncrono.
    container = get_container()
    settings = get_settings()

    sweeper = asyncio.create_task(_auto_encerrar_conversas_loop(container, settings))
    try:
        yield
    finally:
        sweeper.cancel()
        with suppress(asyncio.CancelledError):
            await sweeper


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