from logging.config import fileConfig
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine  # , engine_from_config
from sqlalchemy import pool

from alembic import context

from drivers.sqlalchemy import models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    # Here we are loading the environment variables that are needed to create
    # migration scripts.
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "development":
        dotenv_path = os.path.join(os.path.dirname(__file__), ".env.development")
        load_dotenv(dotenv_path=dotenv_path)
    elif environment == "production":
        dotenv_path = os.path.join(os.path.dirname(__file__), ".env.production")
        load_dotenv(dotenv_path=dotenv_path)

    # Create a synchronous engine using create_engine

    database_user = os.environ.get("MYSQL_DATABASE_USER")
    database_password = os.environ.get("MYSQL_DATABASE_PASSWORD")
    database_host = os.environ.get("MYSQL_DATABASE_HOST")
    database_name = os.environ.get("MYSQL_DATABASE_NAME")
    url = (
        f"mysql+pymysql://{database_user}:"
        f"{database_password}@{database_host}:3306/{database_name}"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # This uses our async engine and fails
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    # Here we are loading the environment variables that are needed to create
    # migration scripts.
    environment = os.getenv("ENVIRONMENT", "development").lower()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

    if environment == "development":
        dotenv_path = os.path.join(parent_dir, ".env.development")
        load_dotenv(dotenv_path=dotenv_path)
    elif environment == "production":
        dotenv_path = os.path.join(parent_dir, ".env.production")
        load_dotenv(dotenv_path=dotenv_path)

    # Create a synchronous engine using create_engine

    database_user = os.environ.get("MYSQL_DATABASE_USER")
    database_password = os.environ.get("MYSQL_DATABASE_PASSWORD")
    database_host = os.environ.get("MYSQL_DATABASE_HOST")
    database_name = os.environ.get("MYSQL_DATABASE_NAME")
    url = (
        f"mysql+pymysql://{database_user}:"
        f"{database_password}@{database_host}:3306/{database_name}"
    )
    print(url)

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
