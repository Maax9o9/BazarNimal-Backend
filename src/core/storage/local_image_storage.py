"""Almacenamiento en disco (src/uploads/images). Para desarrollo o un servidor con disco persistente."""

import mimetypes
from pathlib import Path

import anyio

from src.core.config.settings import Settings
from src.core.logger.logger import get_logger
from src.core.storage.image_processing import (
    PUBLIC_PREFIX,
    is_managed_relative_url,
    new_relative_url,
    reencode_to_webp,
)
from src.shared.contracts.image_storage import IImageStorage

logger = get_logger("storage")

# Algunos sistemas (Windows) no registran .webp: sin esto se serviría como application/octet-stream.
mimetypes.add_type("image/webp", ".webp")


class LocalImageStorage(IImageStorage):
    def __init__(self, settings: Settings) -> None:
        self._root = (settings.uploads_dir / "images").resolve()
        self._base_url = settings.public_base_url.rstrip("/")

    async def save(self, content: bytes, folder: str) -> str:
        relative_url = new_relative_url(folder)
        await anyio.to_thread.run_sync(self._save_sync, content, relative_url)
        return relative_url

    def _save_sync(self, content: bytes, relative_url: str) -> None:
        encoded = reencode_to_webp(content)
        path = self._path_from_url(relative_url)
        assert path is not None
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)

    async def delete(self, relative_url: str | None) -> None:
        path = self._path_from_url(relative_url)
        if path is None:
            return
        try:
            await anyio.to_thread.run_sync(lambda: path.unlink(missing_ok=True))
        except OSError:
            logger.warning("image_delete_failed", extra={"path": relative_url})

    def public_url(self, relative_url: str | None) -> str | None:
        return f"{self._base_url}{relative_url}" if relative_url else None

    def _path_from_url(self, relative_url: str | None) -> Path | None:
        if not is_managed_relative_url(relative_url):
            return None
        candidate = (self._root / relative_url.removeprefix(f"{PUBLIC_PREFIX}/")).resolve()  # type: ignore[union-attr]
        # Evita path traversal: el archivo debe quedar dentro de uploads/images.
        if not candidate.is_relative_to(self._root):
            return None
        return candidate
