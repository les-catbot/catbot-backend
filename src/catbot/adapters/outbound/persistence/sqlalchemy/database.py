from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from catbot.adapters.outbound.persistence.sqlalchemy.models import Base


def create_engine(database_url: str, echo: bool = False):
    return create_async_engine(database_url, echo=echo)


def create_session_factory(database_url: str, echo: bool = False) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(database_url, echo=echo)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_tables(database_url: str, echo: bool = False) -> None:
    engine = create_engine(database_url, echo=echo)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
