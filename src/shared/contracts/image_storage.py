from abc import ABC, abstractmethod

from src.core.errors.exceptions import InvalidDataError


class InvalidImageError(InvalidDataError):
    def __init__(self, message: str = "La imagen no es válida o está dañada") -> None:
        super().__init__(errors=[{"field": "image", "message": message}])


class IImageStorage(ABC):
    @abstractmethod
    async def save(self, content: bytes, folder: str) -> str:
        """Guarda la imagen y devuelve su ruta relativa (por ejemplo, /uploads/images/pets/<uuid>.webp)."""

    @abstractmethod
    async def delete(self, relative_url: str | None) -> None: ...

    @abstractmethod
    def public_url(self, relative_url: str | None) -> str | None: ...
