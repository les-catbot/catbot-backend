from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://catbot:catbot@localhost:5432/catbot"
    DATABASE_ECHO: bool = False

    REPOSITORY_TYPE: str = "memory"

    LLM_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"

    SECRET_KEY: str = "teste"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
