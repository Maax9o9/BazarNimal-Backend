from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, status

from src.core.di.fastapi import inject
from src.features.products.admin.data.dtos.product_admin_dtos import ProductAdminDto
from src.features.products.admin.infrastructure.controllers.product_admin_controller import ProductAdminController
from src.features.products.admin.infrastructure.validators.product_admin_validators import (
    CreateProductForm,
    ProductListQuery,
    UpdateProductForm,
)
from src.shared.middlewares.authorize import require_admin
from src.shared.middlewares.rate_limit import by_user, rate_limit
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, errors
from src.shared.validators.image import MULTIPART

router = APIRouter(
    prefix="/admin/products",
    tags=["Admin - Tienda"],
    dependencies=[Depends(require_admin)],
    responses=errors(401, 403, 422),
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Registrar artículo de la tienda",
    responses=errors(429),
    dependencies=[Depends(rate_limit("upload", by_user))],
)
async def create_product(
    form: Annotated[CreateProductForm, Form(media_type=MULTIPART)],
    admin: CurrentUser = Depends(require_admin),
    controller: ProductAdminController = inject(ProductAdminController),
) -> SuccessResponse[ProductAdminDto]:
    return await controller.create(form, admin)


@router.get("", summary="Listar artículos")
async def list_products(
    query: Annotated[ProductListQuery, Query()],
    controller: ProductAdminController = inject(ProductAdminController),
) -> PaginatedResponse[ProductAdminDto]:
    return await controller.list(query)


@router.get("/{product_id}", summary="Detalle de un artículo", responses=errors(404))
async def get_product(
    product_id: UUID,
    controller: ProductAdminController = inject(ProductAdminController),
) -> SuccessResponse[ProductAdminDto]:
    return await controller.get(str(product_id))


@router.put(
    "/{product_id}",
    summary="Actualizar artículo (la imagen es opcional)",
    responses=errors(404, 429),
    dependencies=[Depends(rate_limit("upload", by_user))],
)
async def update_product(
    product_id: UUID,
    form: Annotated[UpdateProductForm, Form(media_type=MULTIPART)],
    controller: ProductAdminController = inject(ProductAdminController),
) -> SuccessResponse[ProductAdminDto]:
    return await controller.update(str(product_id), form)


@router.delete("/{product_id}", summary="Eliminar artículo", responses=errors(404))
async def delete_product(
    product_id: UUID,
    controller: ProductAdminController = inject(ProductAdminController),
) -> MessageResponse:
    return await controller.delete(str(product_id))
