from src.core.errors.exceptions import NotFoundError
from src.features.products.user.domain.entities.product import Product
from src.features.products.user.domain.repositories.product_catalog_repository import IProductCatalogRepository


class GetProductByIdUseCase:
    def __init__(self, products: IProductCatalogRepository) -> None:
        self._products = products

    async def execute(self, product_id: str) -> Product:
        product = await self._products.find_by_id(product_id)
        if product is None:
            raise NotFoundError("El artículo no existe")
        return product
