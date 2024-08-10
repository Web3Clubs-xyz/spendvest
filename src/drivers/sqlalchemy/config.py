import os
from sqlalchemy.ext.asyncio.session import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine


DATABASE_URL = os.environ.get("MYSQL_DATABASE_URL", "")
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
