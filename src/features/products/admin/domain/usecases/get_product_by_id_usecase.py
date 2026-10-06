from src.core.errors.exceptions import NotFoundError
from src.features.products.admin.domain.entities.product import Product
from src.features.products.admin.domain.repositories.product_repository import IProductRepository


class GetProductByIdUseCase:
    def __init__(self, products: IProductRepository) -> None:
        self._products = products

    async def execute(self, product_id: str) -> Product:
        product = await self._products.find_by_id(product_id)
        if product is None:
            raise NotFoundError("El artículo no existe")
        return product
