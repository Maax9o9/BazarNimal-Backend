from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Query, status

from src.core.di.fastapi import inject
from src.features.posts.user.data.dtos.post_dtos import MyPostDto, PostDto
from src.features.posts.user.infrastructure.controllers.post_controller import PostController
from src.features.posts.user.infrastructure.validators.post_validators import CreatePostForm
from src.shared.middlewares.authorize import require_user
from src.shared.middlewares.rate_limit import by_user, rate_limit
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, errors
from src.shared.validators.common import PaginationQuery
from src.shared.validators.image import MULTIPART

router = APIRouter(prefix="/posts", tags=["Posts"], responses=errors(422))


@router.get("", summary="Publicaciones aprobadas (público)")
async def list_approved_posts(
    query: Annotated[PaginationQuery, Query()],
    controller: PostController = inject(PostController),
) -> PaginatedResponse[PostDto]:
    return await controller.list_approved(query)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Crear publicación (queda pendiente de aprobación)",
    responses=errors(401, 403, 429),
    dependencies=[Depends(require_user), Depends(rate_limit("upload", by_user))],
)
async def create_post(
    form: Annotated[CreatePostForm, Form(media_type=MULTIPART)],
    user: CurrentUser = Depends(require_user),
    controller: PostController = inject(PostController),
) -> SuccessResponse[MyPostDto]:
    return await controller.create(form, user)


@router.get("/me", summary="Mis publicaciones con su estatus", responses=errors(401, 403))
async def my_posts(
    query: Annotated[PaginationQuery, Query()],
    user: CurrentUser = Depends(require_user),
    controller: PostController = inject(PostController),
) -> PaginatedResponse[MyPostDto]:
    return await controller.list_mine(query, user)


@router.get("/{post_id}", summary="Detalle de una publicación aprobada (público)", responses=errors(404))
async def get_approved_post(
    post_id: UUID,
    controller: PostController = inject(PostController),
) -> SuccessResponse[PostDto]:
    return await controller.get_approved(str(post_id))


@router.delete("/{post_id}", summary="Eliminar una publicación propia", responses=errors(401, 403, 404))
async def delete_my_post(
    post_id: UUID,
    user: CurrentUser = Depends(require_user),
    controller: PostController = inject(PostController),
) -> MessageResponse:
    return await controller.delete_mine(str(post_id), user)
