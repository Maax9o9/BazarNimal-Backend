from src.features.products.user.data.dtos.product_dtos import ProductDto
from src.features.products.user.data.mappers.product_mapper import product_to_dto
from src.features.products.user.domain.usecases.get_product_by_id_usecase import GetProductByIdUseCase
from src.features.products.user.domain.usecases.get_products_usecase import GetProductsUseCase
from src.features.products.user.infrastructure.validators.product_validators import ProductListQuery
from src.shared.contracts.image_storage import IImageStorage
from src.shared.utils.responses import PaginatedResponse, SuccessResponse, ok, paginated


class ProductController:
    def __init__(
        self,
        get_products: GetProductsUseCase,
        get_product_by_id: GetProductByIdUseCase,
        storage: IImageStorage,
    ) -> None:
        self._get_products = get_products
        self._get_product_by_id = get_product_by_id
        self._storage = storage

    async def list(self, query: ProductListQuery) -> PaginatedResponse[ProductDto]:
        page = await self._get_products.execute(query.to_filters(), query.to_page_request())
        return paginated([product_to_dto(item, self._storage) for item in page.items], page)

    async def get(self, product_id: str) -> SuccessResponse[ProductDto]:
        return ok(product_to_dto(await self._get_product_by_id.execute(product_id), self._storage))
