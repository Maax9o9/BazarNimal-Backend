"""Procesamiento común a todos los almacenamientos de imágenes.

Cada imagen se decodifica y se vuelve a codificar como WEBP: se eliminan metadatos EXIF
y cualquier contenido que no sea la imagen en sí. El nombre lo genera el servidor (UUID).
"""

import io
import re
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from src.shared.contracts.image_storage import InvalidImageError

# Formato de las rutas guardadas en la base de datos, igual para todos los almacenamientos:
# /uploads/images/<carpeta>/<uuid>.webp
PUBLIC_PREFIX = "/uploads/images"
MAX_DIMENSION = 2048
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
IMAGE_CONTENT_TYPE = "image/webp"

_FOLDER_RE = re.compile(r"^[a-z0-9_-]+$")
_RELATIVE_URL_RE = re.compile(r"^/uploads/images/[a-z0-9_-]+/[0-9a-f]{32}\.webp$")

# Protección contra "decompression bombs".
Image.MAX_IMAGE_PIXELS = 40_000_000


def validate_folder(folder: str) -> None:
    if not _FOLDER_RE.match(folder):
        raise ValueError(f"Carpeta inválida: {folder}")


def new_relative_url(folder: str) -> str:
    validate_folder(folder)
    return f"{PUBLIC_PREFIX}/{folder}/{uuid4().hex}.webp"


def is_managed_relative_url(relative_url: str | None) -> bool:
    """True solo para rutas generadas por el servidor (evita path traversal y borrar cosas ajenas)."""
    return bool(relative_url) and bool(_RELATIVE_URL_RE.match(relative_url or ""))


def reencode_to_webp(content: bytes) -> bytes:
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
