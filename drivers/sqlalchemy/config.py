import asyncio
from collections.abc import AsyncGenerator
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio.session import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.exc import OperationalError


class DbSession:

    def __init__(self):
        self.database_user = os.environ.get("MYSQL_DATABASE_USER")
        self.database_password = os.environ.get("MYSQL_DATABASE_PASSWORD")
        self.database_host = os.environ.get("MYSQL_DATABASE_HOST")
        self.database_name = os.environ.get("MYSQL_DATABASE_NAME")
        self.database_url = (
            f"mysql+aiomysql://{self.database_user}:"
            f"{self.database_password}@{self.database_host}:3306"
        )
        self.engine = create_async_engine(self.database_url)

        self.db_name = "spendvest"

    async def setup(self):
        print("SETTING UP.")

        async def create_database_if_not_exists():
            async with self.engine.connect() as conn:
                try:
                    # Check if the database exists
                    result = await conn.execute(
                        text(f"SHOW DATABASES LIKE '{self.db_name}'")
                    )
                    if not result.fetchone():
                        # Database doesn't exist, create it
                        await conn.execute(text(f"CREATE DATABASE {self.db_name}"))
                except OperationalError as e:
                    print(f"An error occurred: {e}")

        # Run the async function
        await create_database_if_not_exists()

        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession]:
        self.database_url = self.database_url + f"/{self.db_name}"
        print(self.database_url)
        db_engine = create_async_engine(self.database_url + self.db_name)

        AsyncSessionLocal = async_sessionmaker(
            bind=db_engine, expire_on_commit=False, class_=AsyncSession, autoflush=False
        )

        async with AsyncSessionLocal() as session:
            yield session
