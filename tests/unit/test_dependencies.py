import pytest

from catbot.adapters.inbound.api.dependencies import Container
from catbot.config import get_settings


def test_container_openai_exige_api_key(monkeypatch):
    monkeypatch.setenv("REPOSITORY_TYPE", "sqlalchemy")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://catbot:catbot@localhost:5432/catbot",
    )
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        Container()

    get_settings.cache_clear()
