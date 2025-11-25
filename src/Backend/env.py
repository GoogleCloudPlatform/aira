from logging.config import fileConfig

import injector
from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext import asyncio as sqlalchemy_aio

from api import db, dependencies, typings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

fileConfig(config.config_file_name)

target_metadata = db.Base.metadata


@injector.inject
def get_uri(settings: typings.Settings):
    uri = settings.get("database_uri")
    if settings.get("test_mode") == "1":
        uri = settings.get("database_test_uri")
    return uri


container = dependencies.create_container()
engine = container.get(sqlalchemy_aio.AsyncEngine)
uri = container.call_with_injection(get_uri)

config.set_main_option(
    "sqlalchemy.url",
    uri.replace("%", "%%").replace("+asyncpg", ""),
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
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
