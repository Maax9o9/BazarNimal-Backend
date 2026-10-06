"""CORS restringido a los orígenes del frontend (CORS_ORIGINS), con credenciales para las cookies.

Nunca se permite '*': con `allow_credentials=True` el navegador exige orígenes explícitos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config.settings import Settings
from src.core.security.cookies import CSRF_HEADER

ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
ALLOWED_HEADERS = ["Content-Type", CSRF_HEADER]
# Headers que el frontend puede leer (por ejemplo, para mostrar "intenta en N segundos").
EXPOSED_HEADERS = ["RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset", "Retry-After"]
PREFLIGHT_MAX_AGE_SECONDS = 600


def add_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
        expose_headers=EXPOSED_HEADERS,
        max_age=PREFLIGHT_MAX_AGE_SECONDS,
    )
