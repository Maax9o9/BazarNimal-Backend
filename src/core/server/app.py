
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.core.config.settings import Settings, get_settings
from src.core.database.connection import create_engine, create_session_factory
from src.core.database.migrate import run_migrations
from src.core.database.seeders.admin_seeder import seed_admin
from src.core.di.autoload import autoload_modules
from src.core.di.container import Container
from src.core.di.core_module import register_core
from src.core.errors.handlers import register_error_handlers
from src.core.logger.logger import get_logger, setup_logging
from src.core.security.cors import add_cors
from src.core.security.rate_limit import InMemoryRateLimitStore
from src.core.server.middlewares import (
    BodySizeLimitMiddleware,
    CsrfMiddleware,
    GlobalRateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from src.routes.index import API_PREFIX, build_api_router
from src.shared.contracts.field_cipher import IFieldCipher
from src.shared.contracts.password_hasher import IPasswordHasher

logger = get_logger("server")

MULTIPART_OVERHEAD = 64 * 1024

API_DESCRIPTION = """
API de BazarNimal, tienda de mascotas.

- **Adopciones**: perros y gatos en adopción; los usuarios registrados pueden solicitar adoptar.
- **Tienda**: catálogo de artículos para consultar existencia .
- **Posts**: publicaciones de los usuarios (texto e imagen), validadas por el admin.
"""


def create_app(settings: Settings | None = None, *, run_startup_migrations: bool = True) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    rate_limit_store = InMemoryRateLimitStore()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if run_startup_migrations:
            await anyio.to_thread.run_sync(run_migrations, settings)

        engine = create_engine(settings)
        container = Container()
        register_core(
            container,
            settings=settings,
            engine=engine,
            session_factory=create_session_factory(engine),
            rate_limit_store=rate_limit_store,
        )
        autoload_modules(container)
        app.state.container = container

        await seed_admin(engine, settings, container.resolve(IPasswordHasher), container.resolve(IFieldCipher))
        logger.info("server_started", extra={"env": settings.app_env})
        try:
            yield
        finally:
            await engine.dispose()
            logger.info("server_stopped")

    app = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_are_enabled else None,
        redoc_url="/redoc" if settings.docs_are_enabled else None,
        openapi_url="/openapi.json" if settings.docs_are_enabled else None,
        swagger_ui_parameters={"withCredentials": True, "persistAuthorization": True},
    )

    register_error_handlers(app)

    app.add_middleware(
        BodySizeLimitMiddleware,
        json_limit=settings.max_json_body_bytes,
        multipart_limit=settings.max_image_size_bytes + MULTIPART_OVERHEAD,
    )
    if settings.csrf_enabled:
        app.add_middleware(
            CsrfMiddleware,
            exempt_paths={f"{API_PREFIX}/auth/login", f"{API_PREFIX}/auth/register"},
        )
    app.add_middleware(
        GlobalRateLimitMiddleware,
        store=rate_limit_store,
        limit=settings.rate_limit_global,
        window_seconds=settings.rate_limit_global_window_seconds,
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    add_cors(app, settings)

    app.include_router(build_api_router())

    images_dir = settings.uploads_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads/images", StaticFiles(directory=images_dir, html=False), name="uploads")

    @app.get("/health", tags=["Health"], summary="Estado del servicio")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
