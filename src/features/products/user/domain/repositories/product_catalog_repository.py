from abc import ABC, abstractmethod

from src.features.products.user.domain.entities.product import Product, ProductFilters
from src.shared.types.pagination import Page, PageRequest


class IProductCatalogRepository(ABC):
    @abstractmethod
    async def list(self, filters: ProductFilters, page: PageRequest) -> Page[Product]: ...

    @abstractmethod
    async def find_by_id(self, product_id: str) -> Product | None: ...
