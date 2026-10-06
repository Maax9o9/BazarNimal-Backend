from alembic import context
from sqlalchemy import create_engine, pool

from src.core.config.settings import get_settings
from src.core.database.connection import migration_connect_args, migration_database_url

config = context.config
settings = config.attributes.get("settings") or get_settings()


def run_migrations_offline() -> None:
    context.configure(
        url=migration_database_url(settings).render_as_string(hide_password=False),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        migration_database_url(settings),
        poolclass=pool.NullPool,
        connect_args=migration_connect_args(settings),
    )
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
