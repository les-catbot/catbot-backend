from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from catbot.adapters.inbound.api.dependencies import get_container
from catbot.adapters.inbound.api.router import api_router
from catbot.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    return app


app = create_app()
