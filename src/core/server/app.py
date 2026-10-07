
import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anyio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

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
HEALTH_DB_TIMEOUT_SECONDS = 3

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
        if settings.is_production and settings.storage_driver == "local":
            logger.warning(
                "local_image_storage_in_production",
                extra={"hint": "Si el disco del servidor es temporal (Render gratis), usa STORAGE_DRIVER=s3"},
            )
        logger.info("server_started", extra={"env": settings.app_env, "storage": settings.storage_driver})
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
        read_policy=settings.rate_limit_policy("read"),
        write_policy=settings.rate_limit_policy("write"),
    )
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    add_cors(app, settings)

    app.include_router(build_api_router())

    if settings.storage_driver == "local":
        images_dir = settings.uploads_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        app.mount("/uploads/images", StaticFiles(directory=images_dir, html=False), name="uploads")

    @app.get(
        "/health",
        tags=["Health"],
        summary="Estado del servicio y de la conexión a la base de datos",
        responses={503: {"description": "La base de datos no responde"}},
    )
    async def health(request: Request) -> JSONResponse:
        engine: AsyncEngine = request.app.state.container.resolve(AsyncEngine)
        try:
            async with asyncio.timeout(HEALTH_DB_TIMEOUT_SECONDS):
                async with engine.connect() as connection:
                    await connection.execute(text("SELECT 1"))
        except Exception:
            logger.warning("health_database_unavailable")
            return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
        return JSONResponse(content={"status": "ok", "database": "ok"})

    return app
