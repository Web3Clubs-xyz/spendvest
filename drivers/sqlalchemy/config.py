from collections.abc import AsyncGenerator
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio.session import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError


database_user = os.environ.get("MYSQL_DATABASE_USER")
database_password = os.environ.get("MYSQL_DATABASE_PASSWORD")
database_host = os.environ.get("MYSQL_DATABASE_HOST")
database_name = os.environ.get("MYSQL_DATABASE_NAME")
database_url = (
    f"mysql+aiomysql://{database_user}:" f"{database_password}@{database_host}:3306"
)
engine = create_async_engine(database_url)

db_name = "spendvest"


async def setup_db():
    print("SETTING UP.")

    async def create_database_if_not_exists():
        async with engine.connect() as conn:
            try:
                # Check if the database exists
                result = await conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
                if not result.fetchone():
                    # Database doesn't exist, create it
                    await conn.execute(text(f"CREATE DATABASE {db_name}"))
            except OperationalError as e:
                print(f"An error occurred: {e}")

    # Run the async function
    await create_database_if_not_exists()

    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    full_database_url = database_url + f"/{db_name}"
    db_engine = create_async_engine(full_database_url)

    AsyncSessionLocal = async_sessionmaker(
        bind=db_engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
    )

    async with AsyncSessionLocal() as session:
        yield session
