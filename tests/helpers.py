"""Entorno y utilidades compartidas de las pruebas.

Se importa siempre como `tests.helpers` (desde conftest y desde las pruebas) para que el
entorno se configure una sola vez. Los valores son exclusivos de pruebas, nunca de un .env real.
"""

import base64
import io
import os
import tempfile
from pathlib import Path

TMP_DIR = Path(tempfile.mkdtemp(prefix="bazarnimal-tests-"))
UPLOADS_IMAGES_DIR = TMP_DIR / "uploads" / "images"

TEST_ADMIN_EMAIL = "admin@bazarnimal-test.com"
TEST_ADMIN_PASSWORD = "Admin#Test2026"
TEST_USER_PASSWORD = "Catrina#2026"

TEST_ENV = {
    "APP_ENV": "test",
    "LOG_LEVEL": "WARNING",
    "PUBLIC_BASE_URL": "http://testserver",
    "DOCS_ENABLED": "true",
    "DB_HOST": "127.0.0.1",
    "DB_NAME": "bazarnimal_test",
    "DB_USER": "unused-in-tests",
    "DB_PASSWORD": "unused-in-tests-sqlite",
    "DB_MIGRATION_USER": "unused-in-tests",
    "DB_MIGRATION_PASSWORD": "unused-in-tests-sqlite",
    "DB_URL_OVERRIDE": f"sqlite+aiosqlite:///{(TMP_DIR / 'test.db').as_posix()}",
    "JWT_SECRET": "test-jwt-secret-with-at-least-32-bytes!!",
    "ENCRYPTION_KEYS": "1:" + base64.b64encode(b"k" * 32).decode(),
    "ENCRYPTION_ACTIVE_KEY_VERSION": "1",
    "HMAC_KEY": "test-hmac-secret-with-at-least-32-bytes!",
    "COOKIE_SECURE": "false",
    "COOKIE_SAMESITE": "strict",
    "CORS_ORIGINS": "http://localhost:5173",
    "RATE_LIMIT_READ": "10000",
    "RATE_LIMIT_WRITE": "10000",
    "RATE_LIMIT_LOGIN": "1000",
    "RATE_LIMIT_REGISTER": "1000",
    "RATE_LIMIT_UPLOAD": "1000",
    "MAX_JSON_BODY_KB": "100",
    "UPLOADS_DIR": str(TMP_DIR / "uploads"),
    "ADMIN_NAME": "Admin Pruebas",
    "ADMIN_EMAIL": TEST_ADMIN_EMAIL,
    "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
}

os.environ.update(TEST_ENV)


def settings_kwargs(**overrides: object) -> dict[str, object]:
    """Argumentos para construir Settings(_env_file=None, ...) en pruebas unitarias."""
    values = {key.lower(): value for key, value in TEST_ENV.items()}
    return {**values, **overrides}


def make_png(color: tuple[int, int, int] = (200, 120, 40)) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, format="PNG")
    return buffer.getvalue()
