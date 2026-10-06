from typing import Literal

from pydantic import Field

from src.features.products.user.domain.entities.product import ProductFilters, ProductStatus
from src.shared.validators.common import PaginationQuery


class ProductListQuery(PaginationQuery):
    status: ProductStatus | None = Field(default=None, description="available = hay existencia")
    search: str | None = Field(default=None, max_length=120)
    sort: Literal["created_at", "-created_at", "name", "-name"] = "name"

    def to_filters(self) -> ProductFilters:
        return ProductFilters(status=self.status, search=self.search or None, sort=self.sort)
