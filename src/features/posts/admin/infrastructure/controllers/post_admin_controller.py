from src.features.posts.admin.data.dtos.post_admin_dtos import PostAdminDto
from src.features.posts.admin.data.mappers.post_admin_mapper import post_to_dto
from src.features.posts.admin.domain.usecases.approve_post_usecase import ApprovePostUseCase
from src.features.posts.admin.domain.usecases.delete_post_usecase import DeletePostUseCase
from src.features.posts.admin.domain.usecases.get_post_by_id_usecase import GetPostByIdUseCase
from src.features.posts.admin.domain.usecases.get_posts_usecase import GetPostsUseCase
from src.features.posts.admin.domain.usecases.reject_post_usecase import RejectPostUseCase
from src.features.posts.admin.infrastructure.validators.post_admin_validators import PostListQuery
from src.shared.contracts.image_storage import IImageStorage
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, ok, paginated


class PostAdminController:
    def __init__(
        self,
        get_posts: GetPostsUseCase,
        get_post_by_id: GetPostByIdUseCase,
        approve_post: ApprovePostUseCase,
        reject_post: RejectPostUseCase,
        delete_post: DeletePostUseCase,
        storage: IImageStorage,
    ) -> None:
        self._get_posts = get_posts
        self._get_post_by_id = get_post_by_id
        self._approve_post = approve_post
        self._reject_post = reject_post
        self._delete_post = delete_post
        self._storage = storage

    async def list(self, query: PostListQuery) -> PaginatedResponse[PostAdminDto]:
        page = await self._get_posts.execute(query.to_filters(), query.to_page_request())
        return paginated([post_to_dto(post, self._storage) for post in page.items], page)

    async def get(self, post_id: str) -> SuccessResponse[PostAdminDto]:
        return ok(post_to_dto(await self._get_post_by_id.execute(post_id), self._storage))

    async def approve(self, post_id: str, admin: CurrentUser) -> SuccessResponse[PostAdminDto]:
        post = await self._approve_post.execute(post_id, admin.id)
        return ok(post_to_dto(post, self._storage), "Publicación aprobada")

    async def reject(self, post_id: str, admin: CurrentUser) -> SuccessResponse[PostAdminDto]:
        post = await self._reject_post.execute(post_id, admin.id)
        return ok(post_to_dto(post, self._storage), "Publicación rechazada")

    async def delete(self, post_id: str) -> MessageResponse:
        await self._delete_post.execute(post_id)
        return MessageResponse(message="Publicación eliminada")
