"""Pool de conexiones MySQL (SQLAlchemy async + aiomysql)."""

import ssl

from sqlalchemy import URL, make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.core.config.settings import Settings

# Todas las fechas se guardan en UTC.
_MYSQL_INIT_COMMAND = "SET time_zone = '+00:00'"


def _ssl_args(settings: Settings) -> dict:
    if not settings.db_ssl_ca:
        return {}
    context = ssl.create_default_context(cafile=settings.db_ssl_ca)
    return {"ssl": context}


def app_database_url(settings: Settings) -> URL:
    if settings.db_url_override:
        return make_url(settings.db_url_override)
    return URL.create(
        "mysql+aiomysql",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        query={"charset": "utf8mb4"},
    )


def migration_database_url(settings: Settings) -> URL:
    """Usuario con más privilegios, solo para migraciones (driver síncrono)."""
    if settings.db_url_override:
        url = make_url(settings.db_url_override)
        return url.set(drivername=url.drivername.split("+")[0])
    return URL.create(
        "mysql+pymysql",
        username=settings.db_migration_user,
        password=settings.db_migration_password.get_secret_value(),
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        query={"charset": "utf8mb4"},
    )


def migration_connect_args(settings: Settings) -> dict:
    if settings.db_url_override:
        return {}
    return {"init_command": _MYSQL_INIT_COMMAND, **_ssl_args(settings)}


def create_engine(settings: Settings) -> AsyncEngine:
    url = app_database_url(settings)
    if url.get_backend_name() == "sqlite":
        return create_async_engine(url)
    return create_async_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_pool_size,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"init_command": _MYSQL_INIT_COMMAND, **_ssl_args(settings)},
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
