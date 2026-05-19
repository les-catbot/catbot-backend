import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["REPOSITORY_TYPE"] = "memory"
os.environ["LLM_PROVIDER"] = "stub"
os.environ["EMBEDDING_PROVIDER"] = "stub"
os.environ["EMBEDDING_TYPE"] = "stub"
os.environ["OPENAI_API_KEY"] = "test-key"

from catbot.adapters.inbound.api import dependencies as deps
from catbot.adapters.inbound.api.dependencies import Container
from catbot.main import create_app


@pytest.fixture
def container() -> Container:
    return Container()


@pytest.fixture
def app(container: Container):
    application = create_app()
    deps._container = container
    yield application
    deps._container = None


@pytest.fixture
async def client(app) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
