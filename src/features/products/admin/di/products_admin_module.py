from src.core.di.container import Container, Lifetime
from src.features.products.admin.data.repositories.product_repository_impl import ProductRepositoryImpl
from src.features.products.admin.domain.repositories.product_repository import IProductRepository
from src.features.products.admin.domain.usecases.create_product_usecase import CreateProductUseCase
from src.features.products.admin.domain.usecases.delete_product_usecase import DeleteProductUseCase
from src.features.products.admin.domain.usecases.get_product_by_id_usecase import GetProductByIdUseCase
from src.features.products.admin.domain.usecases.get_products_usecase import GetProductsUseCase
from src.features.products.admin.domain.usecases.update_product_usecase import UpdateProductUseCase
from src.features.products.admin.infrastructure.controllers.product_admin_controller import ProductAdminController


def register(container: Container) -> None:
    container.register(IProductRepository, ProductRepositoryImpl, lifetime=Lifetime.SCOPED)

    for usecase in (
        CreateProductUseCase,
        GetProductsUseCase,
        GetProductByIdUseCase,
        UpdateProductUseCase,
        DeleteProductUseCase,
    ):
        container.register(usecase)

    container.register(ProductAdminController)
