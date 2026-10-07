"""Almacenamiento compatible con S3 (Cloudflare R2, AWS S3, Backblaze B2, MinIO...).

Se usa en servidores con disco temporal (por ejemplo, el plan gratis de Render), donde los
archivos locales se pierden en cada reinicio. Las rutas en la base de datos tienen el mismo
formato que en el almacenamiento local, así que se puede cambiar de uno a otro.
"""

import anyio
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.core.config.settings import Settings
from src.core.logger.logger import get_logger
from src.core.storage.image_processing import (
    IMAGE_CONTENT_TYPE,
    is_managed_relative_url,
    new_relative_url,
    reencode_to_webp,
)
from src.shared.contracts.image_storage import IImageStorage

logger = get_logger("storage")

CACHE_CONTROL = "public, max-age=31536000, immutable"  # el nombre es único: nunca cambia el contenido


class S3ImageStorage(IImageStorage):
    def __init__(self, settings: Settings) -> None:
        assert settings.s3_bucket and settings.s3_access_key_id and settings.s3_secret_access_key
        assert settings.s3_public_base_url
        self._bucket = settings.s3_bucket
        self._public_base_url = settings.s3_public_base_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_access_key.get_secret_value(),
            config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
        )

    async def save(self, content: bytes, folder: str) -> str:
        relative_url = new_relative_url(folder)
        await anyio.to_thread.run_sync(self._save_sync, content, relative_url)
        return relative_url

    def _save_sync(self, content: bytes, relative_url: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=_key(relative_url),
            Body=reencode_to_webp(content),
            ContentType=IMAGE_CONTENT_TYPE,
            CacheControl=CACHE_CONTROL,
        )

    async def delete(self, relative_url: str | None) -> None:
        if not is_managed_relative_url(relative_url):
            return
        try:
            await anyio.to_thread.run_sync(
                lambda: self._client.delete_object(Bucket=self._bucket, Key=_key(relative_url))  # type: ignore[arg-type]
            )
        except (BotoCoreError, ClientError):
            logger.warning("image_delete_failed", extra={"path": relative_url})

    def public_url(self, relative_url: str | None) -> str | None:
        return f"{self._public_base_url}{relative_url}" if relative_url else None


def _key(relative_url: str) -> str:
    # "/uploads/images/pets/<uuid>.webp" -> "uploads/images/pets/<uuid>.webp"
    return relative_url.lstrip("/")
