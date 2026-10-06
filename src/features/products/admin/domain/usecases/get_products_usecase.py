from src.features.products.admin.domain.entities.product import Product, ProductFilters
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.shared.types.pagination import Page, PageRequest


class GetProductsUseCase:
    def __init__(self, products: IProductRepository) -> None:
        self._products = products

    async def execute(self, filters: ProductFilters, page: PageRequest) -> Page[Product]:
        return await self._products.list(filters, page)
