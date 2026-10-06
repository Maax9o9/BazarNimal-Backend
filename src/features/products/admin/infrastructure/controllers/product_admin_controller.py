from src.features.products.admin.data.dtos.product_admin_dtos import ProductAdminDto
from src.features.products.admin.data.mappers.product_admin_mapper import product_to_dto
from src.features.products.admin.domain.usecases.create_product_usecase import (
    CreateProductInput,
    CreateProductUseCase,
)
from src.features.products.admin.domain.usecases.delete_product_usecase import DeleteProductUseCase
from src.features.products.admin.domain.usecases.get_product_by_id_usecase import GetProductByIdUseCase
from src.features.products.admin.domain.usecases.get_products_usecase import GetProductsUseCase
from src.features.products.admin.domain.usecases.update_product_usecase import (
    UpdateProductInput,
    UpdateProductUseCase,
)
from src.features.products.admin.infrastructure.validators.product_admin_validators import (
    CreateProductForm,
    ProductListQuery,
    UpdateProductForm,
)
from src.shared.contracts.image_storage import IImageStorage
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, ok, paginated


class ProductAdminController:
    def __init__(
        self,
        create_product: CreateProductUseCase,
        get_products: GetProductsUseCase,
        get_product_by_id: GetProductByIdUseCase,
        update_product: UpdateProductUseCase,
        delete_product: DeleteProductUseCase,
        storage: IImageStorage,
    ) -> None:
        self._create_product = create_product
        self._get_products = get_products
        self._get_product_by_id = get_product_by_id
        self._update_product = update_product
        self._delete_product = delete_product
        self._storage = storage

    async def create(self, form: CreateProductForm, admin: CurrentUser) -> SuccessResponse[ProductAdminDto]:
        product = await self._create_product.execute(
            CreateProductInput(data=form.to_domain(), image=await form.image.read(), admin_id=admin.id)
        )
        return ok(product_to_dto(product, self._storage), "Artículo registrado")

    async def list(self, query: ProductListQuery) -> PaginatedResponse[ProductAdminDto]:
        page = await self._get_products.execute(query.to_filters(), query.to_page_request())
        return paginated([product_to_dto(item, self._storage) for item in page.items], page)

    async def get(self, product_id: str) -> SuccessResponse[ProductAdminDto]:
        return ok(product_to_dto(await self._get_product_by_id.execute(product_id), self._storage))

    async def update(self, product_id: str, form: UpdateProductForm) -> SuccessResponse[ProductAdminDto]:
        image = await form.image.read() if form.image else None
        product = await self._update_product.execute(
            UpdateProductInput(product_id=product_id, data=form.to_domain(), image=image)
        )
        return ok(product_to_dto(product, self._storage), "Artículo actualizado")

    async def delete(self, product_id: str) -> MessageResponse:
        await self._delete_product.execute(product_id)
        return MessageResponse(message="Artículo eliminado")
