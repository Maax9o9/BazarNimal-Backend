from dataclasses import dataclass

from src.features.products.admin.domain.entities.product import Product, ProductData
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.shared.contracts.image_storage import IImageStorage

IMAGE_FOLDER = "products"


@dataclass(frozen=True, slots=True)
class CreateProductInput:
    data: ProductData
    image: bytes
    admin_id: str


class CreateProductUseCase:
    def __init__(self, products: IProductRepository, storage: IImageStorage) -> None:
        self._products = products
        self._storage = storage

    async def execute(self, data: CreateProductInput) -> Product:
        image_url = await self._storage.save(data.image, IMAGE_FOLDER)
        try:
            return await self._products.create(data.data, image_url, data.admin_id)
        except Exception:
            await self._storage.delete(image_url)
            raise
