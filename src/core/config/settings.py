"""Variables de entorno tipadas y validadas al arrancar.

Si falta una variable crítica o tiene un valor inseguro, la aplicación no arranca.
Los valores que dependen del ambiente (URLs, orígenes, host de BD) no tienen valor por
defecto: deben venir del .env para que producción nunca use "localhost" en silencio.
"""

import base64
import binascii
import re
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, EmailStr, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.shared.validators.common import check_password_policy

BASE_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = BASE_DIR / "src"

MIN_SECRET_BYTES = 32  # 256 bits
MIN_DB_PASSWORD_LENGTH = 16
# Valores de ejemplo de .env.example / bd/bazarnimal.sql que nunca deben usarse de verdad.
_PLACEHOLDER_RE = re.compile(r"cambia|genera|change.?me|example|placeholder", re.IGNORECASE)
_ORIGIN_RE = re.compile(r"^https?://[A-Za-z0-9.\-]+(:\d{1,5})?$")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _reject_placeholder(name: str, value: str) -> None:
    if _PLACEHOLDER_RE.search(value):
        raise ValueError(f"{name} tiene un valor de ejemplo; genera uno real (scripts/generate_secrets.py)")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,  # VAR= vacío cuenta como no definido (los obligatorios fallan)
        extra="ignore",
        populate_by_name=True,
        # Los errores de validación nunca muestran los valores recibidos (pueden ser secretos).
        hide_input_in_errors=True,
    )

    # Aplicación
    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "BazarNimal API"
    public_base_url: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # Swagger/ReDoc. Si no se define: habilitado fuera de producción, deshabilitado en producción.
    docs_enabled: bool | None = None

    # Servidor (python src/main.py)
    app_host: str = "127.0.0.1"
    # Render (y otros PaaS) asignan el puerto en la variable PORT.
    app_port: int = Field(default=8000, ge=1, le=65535, validation_alias=AliasChoices("APP_PORT", "PORT"))
    app_reload: bool = False
    # IPs de proxies confiables para leer X-Forwarded-For (IP real del cliente).
    forwarded_allow_ips: str = "127.0.0.1"

    # Base de datos
    db_host: str
    db_port: int = 3306
    db_name: str
    db_user: str
    db_password: SecretStr
    db_migration_user: str
    db_migration_password: SecretStr
    # Ruta al certificado CA de MySQL para conectar por TLS (Aiven lo exige).
    db_ssl_ca: str | None = None
    # Alternativa sin archivo: el contenido del certificado CA (-----BEGIN CERTIFICATE----- ...).
    # Si está definido, tiene prioridad sobre DB_SSL_CA.
    db_ssl_ca_pem: str | None = None
    db_pool_size: int = Field(default=10, ge=1, le=100)
    # Solo para pruebas automatizadas (por ejemplo, SQLite). Prohibido fuera de app_env=test.
    db_url_override: str | None = None

    # JWT
    jwt_secret: SecretStr
    access_token_ttl_user_minutes: int = Field(default=15, ge=1)
    access_token_ttl_admin_minutes: int = Field(default=120, ge=1)
    refresh_token_ttl_days: int = Field(default=7, ge=1)

    # Cookies
    cookie_secure: bool = True
    cookie_samesite: Literal["strict", "lax", "none"] = "strict"
    cookie_domain: str | None = None

    # Cifrado de datos personales
    encryption_keys: SecretStr  # "1:<base64 de 32 bytes>,2:<base64 de 32 bytes>"
    encryption_active_key_version: int = 1
    hmac_key: SecretStr

    # CORS (orígenes del frontend separados por coma)
    cors_origins: str

    # Protección del login
    login_max_failed_attempts: int = Field(default=5, ge=1)
    login_lock_minutes: int = Field(default=15, ge=1)

    # Rate limit (peticiones, ventana en segundos)
    # Límite general por IP, separado en lectura (GET/HEAD) y escritura (POST/PUT/PATCH/DELETE).
    rate_limit_read: int = Field(default=600, ge=1)
    rate_limit_read_window_seconds: int = Field(default=900, ge=1)
    rate_limit_write: int = Field(default=100, ge=1)
    rate_limit_write_window_seconds: int = Field(default=900, ge=1)
    rate_limit_login: int = 5
    rate_limit_login_window_seconds: int = 900
    rate_limit_register: int = 5
    rate_limit_register_window_seconds: int = 3600
    rate_limit_upload: int = 20
    rate_limit_upload_window_seconds: int = 3600

    # Límites de peticiones
    max_json_body_kb: int = Field(default=100, ge=1, le=1024)
    max_image_size_mb: int = Field(default=5, ge=1, le=20)
    uploads_dir: Path = SRC_DIR / "uploads"

    # Almacenamiento de imágenes: "local" (disco) o "s3" (Cloudflare R2 u otro compatible con S3).
    storage_driver: Literal["local", "s3"] = "local"
    s3_endpoint_url: str | None = None  # R2: https://<account_id>.r2.cloudflarestorage.com
    s3_region: str = "auto"
    s3_bucket: str | None = None
    s3_access_key_id: SecretStr | None = None
    s3_secret_access_key: SecretStr | None = None
    s3_public_base_url: str | None = None  # URL pública del bucket (r2.dev o dominio propio)

    # Administrador inicial (seeder)
    admin_name: str | None = None
    admin_email: EmailStr | None = None
    admin_password: SecretStr | None = None

    @field_validator("jwt_secret", "hmac_key")
    @classmethod
    def _secret_strength(cls, value: SecretStr, info) -> SecretStr:
        secret = value.get_secret_value()
        _reject_placeholder(info.field_name.upper(), secret)
        if len(secret.encode()) < MIN_SECRET_BYTES:
            raise ValueError(f"debe tener al menos {MIN_SECRET_BYTES} bytes")
        return value

    @field_validator("db_password", "db_migration_password")
    @classmethod
    def _db_password_strength(cls, value: SecretStr, info) -> SecretStr:
        password = value.get_secret_value()
        _reject_placeholder(info.field_name.upper(), password)
        if len(password) < MIN_DB_PASSWORD_LENGTH:
            raise ValueError(f"debe tener al menos {MIN_DB_PASSWORD_LENGTH} caracteres")
        return value

    @field_validator("admin_password")
    @classmethod
    def _admin_password_strength(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            _reject_placeholder("ADMIN_PASSWORD", value.get_secret_value())
            check_password_policy(value.get_secret_value())
        return value

    @field_validator("db_ssl_ca_pem")
    @classmethod
    def _normalize_pem(cls, value: str | None) -> str | None:
        if value is None:
            return None
        # Algunos paneles guardan los saltos de línea como el texto "\n" (barra + n).
        return value.replace("\\n", "\n").strip() + "\n"

    @field_validator("cors_origins")
    @classmethod
    def _valid_origins(cls, value: str) -> str:
        # El navegador envía el origen sin barra final: "https://sitio.com/" se normaliza a "https://sitio.com".
        origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("define al menos un origen del frontend")
        for origin in origins:
            if "*" in origin:
                raise ValueError("no se permite '*' cuando se usan cookies")
            if not _ORIGIN_RE.match(origin):
                raise ValueError(f"origen inválido '{origin}' (formato: http(s)://host[:puerto], sin ruta)")
        return ",".join(origins)

    @model_validator(mode="after")
    def _check_consistency(self) -> "Settings":
        keys = self.encryption_key_map
        if self.encryption_active_key_version not in keys:
            raise ValueError("ENCRYPTION_ACTIVE_KEY_VERSION no existe en ENCRYPTION_KEYS")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("COOKIE_SAMESITE=none requiere COOKIE_SECURE=true")
        if self.db_url_override and self.app_env != "test":
            raise ValueError("DB_URL_OVERRIDE solo se permite con APP_ENV=test")
        if self.db_ssl_ca_pem:
            if "-----BEGIN CERTIFICATE-----" not in self.db_ssl_ca_pem:
                raise ValueError("DB_SSL_CA_PEM no contiene un certificado (falta -----BEGIN CERTIFICATE-----)")
        elif self.db_ssl_ca and not Path(self.db_ssl_ca).is_file():
            raise ValueError(f"DB_SSL_CA no existe: {self.db_ssl_ca} (o define DB_SSL_CA_PEM con el certificado)")
        if self.storage_driver == "s3":
            required = {
                "S3_ENDPOINT_URL": self.s3_endpoint_url,
                "S3_BUCKET": self.s3_bucket,
                "S3_ACCESS_KEY_ID": self.s3_access_key_id,
                "S3_SECRET_ACCESS_KEY": self.s3_secret_access_key,
                "S3_PUBLIC_BASE_URL": self.s3_public_base_url,
            }
            missing = [name for name, value in required.items() if not value]
            if missing:
                raise ValueError(f"STORAGE_DRIVER=s3 requiere: {', '.join(missing)}")
        if self.is_production:
            if not self.cookie_secure:
                raise ValueError("En producción COOKIE_SECURE debe ser true")
            if not self.public_base_url.startswith("https://"):
                raise ValueError("En producción PUBLIC_BASE_URL debe usar https://")
            if any(origin.startswith("http://") for origin in self.cors_origin_list):
                raise ValueError("En producción CORS_ORIGINS solo admite orígenes https://")
            if self.db_host not in _LOCAL_HOSTS and not (self.db_ssl_ca or self.db_ssl_ca_pem):
                raise ValueError("En producción con MySQL remoto se requiere DB_SSL_CA o DB_SSL_CA_PEM (TLS)")
            if self.app_reload:
                raise ValueError("APP_RELOAD no se permite en producción")
            if self.storage_driver == "s3" and not (self.s3_public_base_url or "").startswith("https://"):
                raise ValueError("En producción S3_PUBLIC_BASE_URL debe usar https://")
        return self

    @cached_property
    def encryption_key_map(self) -> dict[int, bytes]:
        keys: dict[int, bytes] = {}
        for item in self.encryption_keys.get_secret_value().split(","):
            version, _, encoded = item.strip().partition(":")
            try:
                key = base64.b64decode(encoded, validate=True)
                parsed_version = int(version)
            except (binascii.Error, ValueError) as exc:
                raise ValueError("ENCRYPTION_KEYS tiene un formato inválido") from exc
            if len(key) != 32:
                raise ValueError("Cada llave de ENCRYPTION_KEYS debe medir 32 bytes (AES-256)")
            keys[parsed_version] = key
        if not keys:
            raise ValueError("ENCRYPTION_KEYS está vacío")
        return keys

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def csrf_enabled(self) -> bool:
        return self.cookie_samesite == "none"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def docs_are_enabled(self) -> bool:
        return self.docs_enabled if self.docs_enabled is not None else not self.is_production

    @property
    def max_json_body_bytes(self) -> int:
        return self.max_json_body_kb * 1024

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024

    def rate_limit_policy(self, name: str) -> tuple[int, int]:
        policies = {
            "read": (self.rate_limit_read, self.rate_limit_read_window_seconds),
            "write": (self.rate_limit_write, self.rate_limit_write_window_seconds),
            "login": (self.rate_limit_login, self.rate_limit_login_window_seconds),
            "register": (self.rate_limit_register, self.rate_limit_register_window_seconds),
            "upload": (self.rate_limit_upload, self.rate_limit_upload_window_seconds),
        }
        return policies[name]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
