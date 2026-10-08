import base64
from abc import ABC, abstractmethod

import pytest

from src.core.config.settings import Settings
from src.core.di.container import Container, DependencyError, Lifetime
from src.core.security.aes_gcm_field_cipher import AesGcmFieldCipher, DecryptionError
from src.core.security.rate_limit import InMemoryRateLimitStore, rate_limit_headers
from src.shared.utils.sql import like_pattern
from src.shared.validators.image import detect_image_mime
from tests.helpers import settings_kwargs


def _settings(**overrides) -> Settings:
    defaults = {"encryption_keys": "1:" + base64.b64encode(b"a" * 32).decode()}
    return Settings(_env_file=None, **settings_kwargs(**{**defaults, **overrides}))


# --- DI ---------------------------------------------------------------------


class IGreeter(ABC):
    @abstractmethod
    def greet(self) -> str: ...


class Greeter(IGreeter):
    def greet(self) -> str:
        return "hola"


class Service:
    def __init__(self, greeter: IGreeter) -> None:
        self.greeter = greeter


def test_container_autowires_interfaces_and_respects_lifetimes():
    container = Container()
    container.register(IGreeter, Greeter, lifetime=Lifetime.SCOPED)
    container.register(Service)
    scope_a, scope_b = container.create_scope(), container.create_scope()
    assert scope_a.resolve(Service).greeter is scope_a.resolve(Service).greeter
    assert scope_a.resolve(IGreeter) is not scope_b.resolve(IGreeter)
    assert scope_a.resolve(Service) is not scope_a.resolve(Service)  # transient


def test_singleton_cannot_capture_scoped_dependency():
    container = Container()
    container.register(IGreeter, Greeter, lifetime=Lifetime.SCOPED)
    container.register(Service, lifetime=Lifetime.SINGLETON)
    with pytest.raises(DependencyError):
        container.create_scope().resolve(Service)


def test_all_feature_modules_resolve():
    """Cada controlador registrado se puede construir con sus dependencias."""
    from unittest.mock import MagicMock

    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

    from src.core.di.autoload import autoload_modules
    from src.core.di.core_module import register_core

    container = Container()
    register_core(
        container,
        settings=_settings(),
        engine=MagicMock(spec=AsyncEngine),
        session_factory=lambda: MagicMock(spec=AsyncSession),
        rate_limit_store=InMemoryRateLimitStore(),
    )
    modules = autoload_modules(container)
    assert len(modules) == 7
    scope = container.create_scope()
    controllers = [key for key in container._registrations if getattr(key, "__name__", "").endswith("Controller")]
    assert len(controllers) == 8
    for controller in controllers:
        scope.resolve(controller)


# --- Configuración ----------------------------------------------------------


def test_settings_reject_insecure_values():
    with pytest.raises(ValueError):
        _settings(jwt_secret="corto")
    with pytest.raises(ValueError):
        _settings(cors_origins="*")
    with pytest.raises(ValueError):
        _settings(cookie_samesite="none", cookie_secure=False)
    with pytest.raises(ValueError):
        _settings(encryption_keys="1:" + base64.b64encode(b"short").decode())
    with pytest.raises(ValueError):
        _settings(cors_origins="http://localhost:5173/app")


def test_settings_reject_example_and_weak_values():
    with pytest.raises(ValueError, match="valor de ejemplo"):
        _settings(jwt_secret="genera_un_secreto_de_al_menos_32_bytes")
    with pytest.raises(ValueError, match="valor de ejemplo"):
        _settings(db_password="cambia_esta_contrasena_app")
    with pytest.raises(ValueError):
        _settings(db_password="corta")
    with pytest.raises(ValueError, match="valor de ejemplo"):
        _settings(admin_password="cambia_esta_contrasena_admin")
    with pytest.raises(ValueError, match="mayúscula"):
        _settings(admin_password="adminadmin123!")


def test_production_requires_https_and_tls():
    prod = {
        "app_env": "production",
        "db_url_override": None,
        "docs_enabled": None,
        "cookie_secure": True,
        "public_base_url": "https://api.bazarnimal.com",
        "cors_origins": "https://bazarnimal.com",
    }
    assert _settings(**prod).docs_are_enabled is False
    with pytest.raises(ValueError, match="https"):
        _settings(**{**prod, "public_base_url": "http://api.bazarnimal.com"})
    with pytest.raises(ValueError, match="https"):
        _settings(**{**prod, "cors_origins": "http://bazarnimal.com"})
    with pytest.raises(ValueError, match="DB_SSL_CA"):
        _settings(**{**prod, "db_host": "db.bazarnimal.com"})


# --- Cifrado ----------------------------------------------------------------


def test_cipher_roundtrip_context_binding_and_key_rotation():
    old = AesGcmFieldCipher(_settings())
    value = old.encrypt("5512345678", "users.phone")
    assert value.startswith("v1:") and "5512345678" not in value
    assert old.encrypt("5512345678", "users.phone") != value  # IV aleatorio
    assert old.decrypt(value, "users.phone") == "5512345678"
    with pytest.raises(DecryptionError):
        old.decrypt(value, "users.email")

    rotated = AesGcmFieldCipher(
        _settings(
            encryption_keys=f"1:{base64.b64encode(b'a' * 32).decode()},2:{base64.b64encode(b'b' * 32).decode()}",
            encryption_active_key_version=2,
        )
    )
    assert rotated.decrypt(value, "users.phone") == "5512345678"
    assert rotated.needs_reencryption(value)
    assert rotated.encrypt("x", "c").startswith("v2:")
    assert rotated.blind_index("ana@example.com") == old.blind_index("ana@example.com")


# --- Rate limit -------------------------------------------------------------


async def test_rate_limit_store_blocks_and_resets():
    now = [0.0]
    store = InMemoryRateLimitStore(clock=lambda: now[0])
    results = [await store.hit("k", 2, 60) for _ in range(3)]
    assert [r.allowed for r in results] == [True, True, False]
    headers = rate_limit_headers(results[-1])
    assert headers["RateLimit-Limit"] == "2"
    assert headers["RateLimit-Remaining"] == "0"
    assert headers["Retry-After"] == headers["RateLimit-Reset"] == "60"
    now[0] = 61
    assert (await store.hit("k", 2, 60)).allowed


# --- Utilidades -------------------------------------------------------------


def test_detect_image_mime_uses_magic_bytes():
    assert detect_image_mime(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert detect_image_mime(b"\x89PNG\r\n\x1a\nrest") == "image/png"
    assert detect_image_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert detect_image_mime(b"GIF89a") is None
    assert detect_image_mime(b"<svg onload=alert(1)>") is None


def test_like_pattern_escapes_wildcards():
    assert like_pattern("100%_off!") == "%100!%!_off!!%"


def test_render_like_production_config(tmp_path, monkeypatch):
    ca = tmp_path / "aiven-ca.pem"
    ca.write_text("certificado de prueba")
    monkeypatch.delenv("APP_PORT", raising=False)
    monkeypatch.setenv("PORT", "10000")  # Render asigna el puerto en PORT
    settings = _settings(
        app_env="production",
        db_url_override=None,
        docs_enabled=None,
        app_host="0.0.0.0",
        cookie_secure=True,
        forwarded_allow_ips="*",
        public_base_url="https://bazarnimal-api.onrender.com",
        cors_origins="https://bazarnimal.vercel.app",
        db_host="mysql-bazarnimal.aivencloud.com",
        db_ssl_ca=str(ca),
        storage_driver="s3",
        s3_endpoint_url="https://account123.r2.cloudflarestorage.com",
        s3_bucket="bazarnimal-images",
        s3_access_key_id="key",
        s3_secret_access_key="secret",
        s3_public_base_url="https://pub-123.r2.dev",
    )
    assert settings.app_port == 10000
    assert settings.docs_are_enabled is False
    with pytest.raises(ValueError, match="DB_SSL_CA no existe"):
        _settings(db_ssl_ca=str(tmp_path / "no-existe.pem"))


def test_settings_errors_never_show_secret_values():
    """Un error de configuración (por ejemplo, falta CORS_ORIGINS) no debe imprimir secretos en los logs."""
    from pydantic import ValidationError

    secret_password = "Secreta#Admin2026xyz"
    kwargs = settings_kwargs(admin_password=secret_password)
    kwargs.pop("cors_origins")
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, **{**kwargs, "cors_origins": None})
    message = str(error.value)
    assert "cors_origins" in message
    for secret in (secret_password, kwargs["jwt_secret"], kwargs["hmac_key"], kwargs["db_password"]):
        assert secret not in message


def test_cors_origins_trailing_slash_is_normalized():
    settings = _settings(cors_origins="https://bazar-nimal-frontend.vercel.app/, http://localhost:5173/")
    assert settings.cors_origin_list == ["https://bazar-nimal-frontend.vercel.app", "http://localhost:5173"]
    with pytest.raises(ValueError):
        _settings(cors_origins="https://bazar-nimal-frontend.vercel.app/app")


def test_db_ssl_ca_pem_takes_priority_and_is_normalized(tmp_path):
    pem = "-----BEGIN CERTIFICATE-----\nABC\n-----END CERTIFICATE-----"
    settings = _settings(db_ssl_ca="/etc/secrets/no-existe.pem", db_ssl_ca_pem=pem)
    assert settings.db_ssl_ca_pem == pem + "\n"
    escaped = _settings(db_ssl_ca_pem=pem.replace("\n", "\n"))  # saltos de línea guardados como texto
    assert escaped.db_ssl_ca_pem == pem + "\n"
    with pytest.raises(ValueError, match="DB_SSL_CA_PEM"):
        _settings(db_ssl_ca_pem="no es un certificado")
