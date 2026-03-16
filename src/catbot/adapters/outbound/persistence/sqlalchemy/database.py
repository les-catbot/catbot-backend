from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def create_engine(database_url: str, echo: bool = False):
    return create_async_engine(database_url, echo=echo)


def create_session_factory(database_url: str, echo: bool = False) -> async_sessionmaker[AsyncSession]:
    engine = create_engine(database_url, echo=echo)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
