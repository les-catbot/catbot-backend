from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://catbot:catbot@localhost:5432/catbot"
    DATABASE_ECHO: bool = False

    REPOSITORY_TYPE: str = "sqlalchemy"

    # --- LLM / Embeddings ---
    LLM_PROVIDER: str = "openai"
    EMBEDDING_PROVIDER: str = "openai"
    # Mantido por compatibilidade com .envs antigos que ainda usam EMBEDDING_TYPE.
    EMBEDDING_TYPE: str = "openai"
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"          # Modelo de chat
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # 1536 dimensões

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5

    SECRET_KEY: str = "troque-esta-chave-em-producao"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Encerramento automático de conversas por inatividade ---
    # Tempo (em minutos) sem novas mensagens antes de uma conversa ser encerrada.
    CONVERSA_TIMEOUT_MINUTES: int = 5
    # Frequência (em segundos) com que a varredura de inatividade roda em background.
    CONVERSA_TIMEOUT_CHECK_INTERVAL_SECONDS: int = 60

    # --- Mantidos para compatibilidade com código legado (Ollama) ---
    LLM_BASE_URL: str = "http://localhost:11434"


@lru_cache
def get_settings() -> Settings:
    return Settings()
