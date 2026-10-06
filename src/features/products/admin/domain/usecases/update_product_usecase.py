from dataclasses import dataclass

from src.core.errors.exceptions import NotFoundError
from src.features.products.admin.domain.entities.product import Product, ProductData
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.features.products.admin.domain.usecases.create_product_usecase import IMAGE_FOLDER
from src.shared.contracts.image_storage import IImageStorage


@dataclass(frozen=True, slots=True)
class UpdateProductInput:
    product_id: str
    data: ProductData
    image: bytes | None


class UpdateProductUseCase:
    def __init__(self, products: IProductRepository, storage: IImageStorage) -> None:
        self._products = products
        self._storage = storage

    async def execute(self, data: UpdateProductInput) -> Product:
        current = await self._products.find_by_id(data.product_id)
        if current is None:
            raise NotFoundError("El artículo no existe")

        new_image_url = await self._storage.save(data.image, IMAGE_FOLDER) if data.image else None
        try:
            updated = await self._products.update(
                data.product_id, data.data, new_image_url or current.image_url
            )
        except Exception:
            await self._storage.delete(new_image_url)
            raise

        if new_image_url:
            await self._storage.delete(current.image_url)
        return updated
