"""Registro de los servicios transversales del core en el contenedor."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.core.config.settings import Settings
from src.core.di.container import Container, Lifetime
from src.core.security.aes_gcm_field_cipher import AesGcmFieldCipher
from src.core.security.argon2_password_hasher import Argon2PasswordHasher
from src.core.security.cookies import CookieManager
from src.core.security.jwt_token_service import JwtTokenService
from src.core.security.rate_limit import IRateLimitStore
from src.core.storage.local_image_storage import LocalImageStorage
from src.shared.contracts.field_cipher import IFieldCipher
from src.shared.contracts.image_storage import IImageStorage
from src.shared.contracts.password_hasher import IPasswordHasher
from src.shared.contracts.token_service import ITokenService


async def _close_session(session: AsyncSession) -> None:
    await session.close()


def register_core(
    container: Container,
    *,
    settings: Settings,
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
    rate_limit_store: IRateLimitStore,
) -> None:
    container.register_instance(Settings, settings)
    container.register_instance(AsyncEngine, engine)
    container.register_instance(IRateLimitStore, rate_limit_store)
    container.register(AsyncSession, session_factory, lifetime=Lifetime.SCOPED, dispose=_close_session)

    container.register(IPasswordHasher, Argon2PasswordHasher, lifetime=Lifetime.SINGLETON)
    container.register(ITokenService, JwtTokenService, lifetime=Lifetime.SINGLETON)
    container.register(IFieldCipher, AesGcmFieldCipher, lifetime=Lifetime.SINGLETON)
    container.register(IImageStorage, LocalImageStorage, lifetime=Lifetime.SINGLETON)
    container.register(CookieManager, lifetime=Lifetime.SINGLETON)
