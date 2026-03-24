from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from catbot.adapters.outbound.persistence.sqlalchemy.models import Base


def create_engine(database_url: str, echo: bool = False):
    return create_async_engine(database_url, echo=echo)


def create_session_factory(database_url: str, echo: bool = False) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(database_url, echo=echo)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _run_migrations_sync(database_url: str) -> None:
    import os
    from pathlib import Path

    from alembic import command
    from alembic.config import Config

    cwd = Path.cwd()
    ini_path = cwd / "alembic.ini"
    if not ini_path.exists():
        for candidate in [Path("/app"), Path(__file__).resolve().parents[5]]:
            if (candidate / "alembic.ini").exists():
                ini_path = candidate / "alembic.ini"
                break

    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(ini_path.parent / "alembic"))
    os.environ["DATABASE_URL"] = database_url
    command.upgrade(alembic_cfg, "head")


async def run_migrations(database_url: str) -> None:
    """Run Alembic migrations in a thread to avoid event loop conflicts."""
    import asyncio

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_migrations_sync, database_url)


async def create_tables(database_url: str, echo: bool = False) -> None:
    """Fallback: create tables directly without migration history."""
    engine = create_engine(database_url, echo=echo)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
