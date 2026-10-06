"""Ejecución automática de migraciones al iniciar. Si fallan, la aplicación no arranca."""

from pathlib import Path

from alembic import command
from alembic.config import Config

from src.core.config.settings import Settings
from src.core.logger.logger import get_logger

logger = get_logger("migrations")

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def build_alembic_config(settings: Settings) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.attributes["settings"] = settings
    return config


def run_migrations(settings: Settings) -> None:
    logger.info("migrations_started")
    try:
        command.upgrade(build_alembic_config(settings), "head")
    except Exception:
        logger.exception("migrations_failed")
        raise
    logger.info("migrations_finished")
