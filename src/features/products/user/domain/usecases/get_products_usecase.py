from src.features.products.user.domain.entities.product import Product, ProductFilters
from src.features.products.user.domain.repositories.product_catalog_repository import IProductCatalogRepository
from src.shared.types.pagination import Page, PageRequest


class GetProductsUseCase:
    def __init__(self, products: IProductCatalogRepository) -> None:
        self._products = products

    async def execute(self, filters: ProductFilters, page: PageRequest) -> Page[Product]:
        return await self._products.list(filters, page)
