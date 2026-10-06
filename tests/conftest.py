"""Fixtures de pruebas.

Las pruebas e2e levantan la app completa (migraciones incluidas) contra una base SQLite temporal,
así que no necesitan MySQL. Las pruebas unitarias usan repositorios en memoria.
"""

import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.helpers import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, TEST_USER_PASSWORD, UPLOADS_IMAGES_DIR


@pytest.fixture(scope="session")
def app():
    from src.core.config.settings import get_settings
    from src.core.server.app import create_app

    get_settings.cache_clear()
    return create_app(get_settings())


@pytest.fixture(scope="session")
def client(app) -> Iterator:
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def uploads_dir() -> Path:
    return UPLOADS_IMAGES_DIR


@pytest.fixture
def make_client(app, client):
    """Clientes extra con su propio jar de cookies (comparten la app ya iniciada)."""
    from fastapi.testclient import TestClient

    def _make():
        return TestClient(app)

    return _make


@pytest.fixture
def admin_client(make_client):
    c = make_client()
    r = c.post("/api/v1/auth/login", json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture
def register_user(make_client):
    """Registra un usuario nuevo y devuelve (cliente con sesión iniciada, datos)."""

    def _register(name: str = "Usuario Prueba"):
        c = make_client()
        data = {
            "name": name,
            "email": f"user-{uuid.uuid4().hex[:10]}@bazarnimal-test.com",
            "phone": "5512345678",
            "password": TEST_USER_PASSWORD,
        }
        r = c.post("/api/v1/auth/register", json=data)
        assert r.status_code == 201, r.text
        r = c.post("/api/v1/auth/login", json={"email": data["email"], "password": data["password"]})
        assert r.status_code == 200, r.text
        return c, data

    return _register
