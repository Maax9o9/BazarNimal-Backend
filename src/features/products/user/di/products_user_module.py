from src.core.di.container import Container, Lifetime
from src.features.products.user.data.repositories.product_catalog_repository_impl import (
    ProductCatalogRepositoryImpl,
)
from src.features.products.user.domain.repositories.product_catalog_repository import IProductCatalogRepository
from src.features.products.user.domain.usecases.get_product_by_id_usecase import GetProductByIdUseCase
from src.features.products.user.domain.usecases.get_products_usecase import GetProductsUseCase
from src.features.products.user.infrastructure.controllers.product_controller import ProductController


def register(container: Container) -> None:
    container.register(IProductCatalogRepository, ProductCatalogRepositoryImpl, lifetime=Lifetime.SCOPED)
    container.register(GetProductsUseCase)
    container.register(GetProductByIdUseCase)
    container.register(ProductController)
