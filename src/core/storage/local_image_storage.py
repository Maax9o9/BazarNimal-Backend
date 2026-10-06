
import io
import mimetypes
import re
from pathlib import Path
from uuid import uuid4

import anyio
from PIL import Image, ImageOps, UnidentifiedImageError

from src.core.config.settings import Settings
from src.core.logger.logger import get_logger
from src.shared.contracts.image_storage import IImageStorage, InvalidImageError

logger = get_logger("storage")

PUBLIC_PREFIX = "/uploads/images"
MAX_DIMENSION = 2048
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
_FOLDER_RE = re.compile(r"^[a-z0-9_-]+$")

# Protección contra "decompression bombs".
Image.MAX_IMAGE_PIXELS = 40_000_000

mimetypes.add_type("image/webp", ".webp")


class LocalImageStorage(IImageStorage):
    def __init__(self, settings: Settings) -> None:
        self._root = (settings.uploads_dir / "images").resolve()
        self._base_url = settings.public_base_url.rstrip("/")

    async def save(self, content: bytes, folder: str) -> str:
        if not _FOLDER_RE.match(folder):
            raise ValueError(f"Carpeta inválida: {folder}")
        return await anyio.to_thread.run_sync(self._save_sync, content, folder)

    def _save_sync(self, content: bytes, folder: str) -> str:
        encoded = self._reencode(content)
        directory = self._root / folder
        directory.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid4().hex}.webp"
        (directory / filename).write_bytes(encoded)
        return f"{PUBLIC_PREFIX}/{folder}/{filename}"

    @staticmethod
    def _reencode(content: bytes) -> bytes:
        try:
            with Image.open(io.BytesIO(content)) as source:
                if source.format not in ALLOWED_FORMATS:
                    raise InvalidImageError("Formato no permitido. Usa JPEG, PNG o WEBP")
                source.load()
                image = ImageOps.exif_transpose(source)
                has_alpha = image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))
                output = io.BytesIO()
                image.save(output, format="WEBP", quality=85, method=4)
                return output.getvalue()
        except InvalidImageError:
            raise
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError, SyntaxError) as exc:
            raise InvalidImageError() from exc

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
        if not relative_url or not relative_url.startswith(f"{PUBLIC_PREFIX}/"):
            return None
        candidate = (self._root / relative_url.removeprefix(f"{PUBLIC_PREFIX}/")).resolve()
        # Evita path traversal: el archivo debe quedar dentro de uploads/images.
        if not candidate.is_relative_to(self._root):
            return None
        return candidate
