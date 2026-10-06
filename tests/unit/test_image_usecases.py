from datetime import datetime

import pytest

from src.features.products.admin.domain.entities.product import Product, ProductData, ProductFilters, ProductStatus
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.features.products.admin.domain.usecases.create_product_usecase import (
    CreateProductInput,
    CreateProductUseCase,
)
from src.features.products.admin.domain.usecases.update_product_usecase import (
    UpdateProductInput,
    UpdateProductUseCase,
)
from src.shared.types.pagination import Page, PageRequest
from tests.unit.fakes import FakeImageStorage

DATA = ProductData(name="Croquetas", weight_kg=None, pieces=None, status=ProductStatus.AVAILABLE)


class FailingProductRepository(IProductRepository):
    """Simula que la base de datos falla después de guardar la imagen."""

    def __init__(self, existing: Product | None = None) -> None:
        self.existing = existing

    async def create(self, data: ProductData, image_url: str, created_by: str) -> Product:
        raise RuntimeError("db caída")

    async def find_by_id(self, product_id: str) -> Product | None:
        return self.existing

    async def list(self, filters: ProductFilters, page: PageRequest) -> Page[Product]:
        raise NotImplementedError

    async def update(self, product_id: str, data: ProductData, image_url: str) -> Product:
        raise RuntimeError("db caída")

    async def soft_delete(self, product_id: str) -> None:
        raise NotImplementedError


async def test_create_removes_orphan_image_when_db_fails():
    storage = FakeImageStorage()
    with pytest.raises(RuntimeError):
        await CreateProductUseCase(FailingProductRepository(), storage).execute(
            CreateProductInput(data=DATA, image=b"img", admin_id="admin")
        )
    assert storage.deleted == storage.saved


async def test_update_keeps_previous_image_when_db_fails():
    existing = Product(
        id="p1",
        name="Croquetas",
        image_url="/uploads/images/products/old.webp",
        weight_kg=None,
        pieces=None,
        status=ProductStatus.AVAILABLE,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    storage = FakeImageStorage()
    with pytest.raises(RuntimeError):
        await UpdateProductUseCase(FailingProductRepository(existing), storage).execute(
            UpdateProductInput(product_id="p1", data=DATA, image=b"new")
        )
    assert existing.image_url not in storage.deleted
    assert storage.deleted == storage.saved
