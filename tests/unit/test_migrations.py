"""Las migraciones deben ser reversibles: upgrade -> downgrade -> upgrade."""

import tempfile
from pathlib import Path

import sqlalchemy as sa
from alembic import command

from src.core.config.settings import get_settings
from src.core.database.migrate import build_alembic_config

EXPECTED_TABLES = {"users", "refresh_tokens", "pets", "adoption_requests", "products", "posts"}


def test_migrations_are_reversible():
    db_path = Path(tempfile.mkdtemp()) / "migrations.db"
    settings = get_settings().model_copy(update={"db_url_override": f"sqlite+aiosqlite:///{db_path.as_posix()}"})
    config = build_alembic_config(settings)
    engine = sa.create_engine(f"sqlite:///{db_path.as_posix()}")

    command.upgrade(config, "head")
    assert EXPECTED_TABLES <= set(sa.inspect(engine).get_table_names())

    command.downgrade(config, "base")
    assert not EXPECTED_TABLES & set(sa.inspect(engine).get_table_names())

    command.upgrade(config, "head")
    assert EXPECTED_TABLES <= set(sa.inspect(engine).get_table_names())
    engine.dispose()
