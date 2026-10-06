from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from src.core.di.fastapi import inject
from src.features.products.user.data.dtos.product_dtos import ProductDto
from src.features.products.user.infrastructure.controllers.product_controller import ProductController
from src.features.products.user.infrastructure.validators.product_validators import ProductListQuery
from src.shared.utils.responses import PaginatedResponse, SuccessResponse, errors

router = APIRouter(prefix="/products", tags=["Tienda"], responses=errors(422))


@router.get("", summary="Catálogo de la tienda con su existencia (público)")
async def list_products(
    query: Annotated[ProductListQuery, Query()],
    controller: ProductController = inject(ProductController),
) -> PaginatedResponse[ProductDto]:
    return await controller.list(query)


@router.get("/{product_id}", summary="Detalle de un artículo (público)", responses=errors(404))
async def get_product(
    product_id: UUID,
    controller: ProductController = inject(ProductController),
) -> SuccessResponse[ProductDto]:
    return await controller.get(str(product_id))
