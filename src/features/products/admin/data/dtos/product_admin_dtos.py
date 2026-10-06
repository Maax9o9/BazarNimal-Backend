from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.features.products.admin.domain.entities.product import ProductStatus


class ProductAdminDto(BaseModel):
    id: str
    name: str
    image_url: str | None
    weight_kg: Decimal | None
    pieces: int | None
    status: ProductStatus
    created_at: datetime
    updated_at: datetime
