"""Crea el administrador inicial con las credenciales de las variables de entorno (idempotente)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config.settings import Settings
from src.core.logger.logger import get_logger
from src.shared.contracts.field_cipher import IFieldCipher
from src.shared.contracts.password_hasher import IPasswordHasher
from src.shared.utils.ids import new_id

logger = get_logger("seeders")


async def seed_admin(
    engine: AsyncEngine,
    settings: Settings,
    hasher: IPasswordHasher,
    cipher: IFieldCipher,
) -> None:
    if not (settings.admin_name and settings.admin_email and settings.admin_password):
        logger.warning("admin_seed_skipped", extra={"reason": "ADMIN_NAME/ADMIN_EMAIL/ADMIN_PASSWORD no definidos"})
        return

    email = settings.admin_email.strip().lower()
    email_hash = cipher.blind_index(email)
    async with engine.begin() as connection:
        exists = await connection.scalar(
            text("SELECT 1 FROM users WHERE email_hash = :email_hash"),
            {"email_hash": email_hash},
        )
        if exists:
            return
        await connection.execute(
            text(
                "INSERT INTO users (id, name, email_encrypted, email_hash, password_hash, role, is_active,"
                " failed_login_attempts) VALUES (:id, :name, :email_encrypted, :email_hash, :password_hash,"
                " 'admin', 1, 0)"
            ),
            {
                "id": new_id(),
                "name": settings.admin_name.strip(),
                "email_encrypted": cipher.encrypt(email, "users.email"),
                "email_hash": email_hash,
                "password_hash": await hasher.hash(settings.admin_password.get_secret_value()),
            },
        )
    logger.info("admin_seeded")
