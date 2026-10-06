from src.core.errors.exceptions import NotFoundError
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.shared.contracts.image_storage import IImageStorage


class DeleteProductUseCase:
    def __init__(self, products: IProductRepository, storage: IImageStorage) -> None:
        self._products = products
        self._storage = storage

    async def execute(self, product_id: str) -> None:
        product = await self._products.find_by_id(product_id)
        if product is None:
            raise NotFoundError("El artículo no existe")
        await self._products.soft_delete(product_id)
        await self._storage.delete(product.image_url)
