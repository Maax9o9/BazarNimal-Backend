"""Validación de imágenes subidas: tamaño máximo y MIME real leyendo los magic bytes."""

from typing import Annotated

from fastapi import UploadFile
from pydantic import AfterValidator

from src.core.config.settings import get_settings

_SIGNATURES: tuple[tuple[str, bytes, int], ...] = (
    ("image/jpeg", b"\xff\xd8\xff", 0),
    ("image/png", b"\x89PNG\r\n\x1a\n", 0),
)


def detect_image_mime(head: bytes) -> str | None:
    for mime, signature, offset in _SIGNATURES:
        if head[offset : offset + len(signature)] == signature:
            return mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def _validate_image(upload: UploadFile) -> UploadFile:
    max_bytes = get_settings().max_image_size_bytes
    file = upload.file
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size == 0:
        raise ValueError("La imagen está vacía")
    if size > max_bytes:
        raise ValueError(f"La imagen no debe superar {max_bytes // (1024 * 1024)} MB")
    head = file.read(16)
    file.seek(0)
    if detect_image_mime(head) is None:
        raise ValueError("Formato no permitido. Usa JPEG, PNG o WEBP")
    return upload


ImageUpload = Annotated[UploadFile, AfterValidator(_validate_image)]

# Los formularios con imagen se documentan como multipart para que Swagger permita subir el archivo.
MULTIPART = "multipart/form-data"
