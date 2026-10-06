from abc import ABC, abstractmethod

from src.features.products.admin.domain.entities.product import Product, ProductData, ProductFilters
from src.shared.types.pagination import Page, PageRequest


class IProductRepository(ABC):
    @abstractmethod
    async def create(self, data: ProductData, image_url: str, created_by: str) -> Product: ...

    @abstractmethod
    async def find_by_id(self, product_id: str) -> Product | None: ...

    @abstractmethod
    async def list(self, filters: ProductFilters, page: PageRequest) -> Page[Product]: ...

    @abstractmethod
    async def update(self, product_id: str, data: ProductData, image_url: str) -> Product: ...

    @abstractmethod
    async def soft_delete(self, product_id: str) -> None: ...
