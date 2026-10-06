from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.core.di.fastapi import inject
from src.features.posts.admin.data.dtos.post_admin_dtos import PostAdminDto
from src.features.posts.admin.infrastructure.controllers.post_admin_controller import PostAdminController
from src.features.posts.admin.infrastructure.validators.post_admin_validators import PostListQuery
from src.shared.middlewares.authorize import require_admin
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, errors

router = APIRouter(
    prefix="/admin/posts",
    tags=["Admin - Posts"],
    dependencies=[Depends(require_admin)],
    responses=errors(401, 403, 422),
)


@router.get("", summary="Listar publicaciones para validar (filtra por estatus)")
async def list_posts(
    query: Annotated[PostListQuery, Query()],
    controller: PostAdminController = inject(PostAdminController),
) -> PaginatedResponse[PostAdminDto]:
    return await controller.list(query)


@router.get("/{post_id}", summary="Detalle de una publicación", responses=errors(404))
async def get_post(
    post_id: UUID,
    controller: PostAdminController = inject(PostAdminController),
) -> SuccessResponse[PostAdminDto]:
    return await controller.get(str(post_id))


@router.patch("/{post_id}/approve", summary="Aprobar publicación (se muestra en la página)", responses=errors(404, 409))
async def approve_post(
    post_id: UUID,
    admin: CurrentUser = Depends(require_admin),
    controller: PostAdminController = inject(PostAdminController),
) -> SuccessResponse[PostAdminDto]:
    return await controller.approve(str(post_id), admin)


@router.patch("/{post_id}/reject", summary="Rechazar publicación", responses=errors(404, 409))
async def reject_post(
    post_id: UUID,
    admin: CurrentUser = Depends(require_admin),
    controller: PostAdminController = inject(PostAdminController),
) -> SuccessResponse[PostAdminDto]:
    return await controller.reject(str(post_id), admin)


@router.delete("/{post_id}", summary="Eliminar publicación", responses=errors(404))
async def delete_post(
    post_id: UUID,
    controller: PostAdminController = inject(PostAdminController),
) -> MessageResponse:
    return await controller.delete(str(post_id))
