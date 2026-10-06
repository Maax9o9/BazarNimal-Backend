from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from src.features.products.admin.domain.entities.product import ProductData, ProductFilters, ProductStatus
from src.shared.validators.common import EmptyAsNone, PaginationQuery, StrictSchema
from src.shared.validators.image import ImageUpload

ProductName = Annotated[str, StringConstraints(min_length=1, max_length=120)]
PositiveWeight = Annotated[Decimal, Field(gt=0, le=Decimal("99999.999"), decimal_places=3)]
PositivePieces = Annotated[int, Field(ge=1, le=1_000_000)]
WeightKg = Annotated[PositiveWeight | None, EmptyAsNone]
Pieces = Annotated[PositivePieces | None, EmptyAsNone]


class ProductFormBase(StrictSchema):
    name: ProductName
    weight_kg: WeightKg = Field(default=None, description="Opcional. Peso en kilogramos (ej. 2.5)")
    pieces: Pieces = Field(default=None, description="Opcional. Número de piezas")
    status: ProductStatus = Field(
        default=ProductStatus.AVAILABLE, description="available = disponible, unavailable = no disponible"
    )

    def to_domain(self) -> ProductData:
        return ProductData(name=self.name, weight_kg=self.weight_kg, pieces=self.pieces, status=self.status)


class CreateProductForm(ProductFormBase):
    image: ImageUpload = Field(description="JPEG, PNG o WEBP")


class UpdateProductForm(ProductFormBase):
    image: Annotated[ImageUpload | None, EmptyAsNone] = Field(
        default=None, description="Opcional: si no se envía se conserva la imagen actual"
    )


class ProductListQuery(PaginationQuery):
    status: ProductStatus | None = None
    search: str | None = Field(default=None, max_length=120)
    sort: Literal["created_at", "-created_at", "name", "-name"] = "-created_at"

    def to_filters(self) -> ProductFilters:
        return ProductFilters(status=self.status, search=self.search or None, sort=self.sort)
