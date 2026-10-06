from decimal import Decimal

from pydantic import BaseModel

from src.features.products.user.domain.entities.product import ProductStatus


class ProductDto(BaseModel):
    id: str
    name: str
    image_url: str | None
    weight_kg: Decimal | None
    pieces: int | None
    status: ProductStatus
