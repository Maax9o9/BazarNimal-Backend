from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ProductStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class Product:
    """Vista pública de un artículo: solo informa si hay existencia en tienda."""

    id: str
    name: str
    image_url: str
    weight_kg: Decimal | None
    pieces: int | None
    status: ProductStatus


@dataclass(frozen=True, slots=True)
class ProductFilters:
    status: ProductStatus | None = None
    search: str | None = None
    sort: str | None = None
