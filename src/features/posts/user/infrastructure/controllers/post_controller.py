from src.features.posts.user.data.dtos.post_dtos import MyPostDto, PostDto
from src.features.posts.user.data.mappers.post_mapper import my_post_to_dto, post_to_dto
from src.features.posts.user.domain.usecases.create_post_usecase import CreatePostInput, CreatePostUseCase
from src.features.posts.user.domain.usecases.delete_my_post_usecase import DeleteMyPostUseCase
from src.features.posts.user.domain.usecases.get_approved_post_by_id_usecase import GetApprovedPostByIdUseCase
from src.features.posts.user.domain.usecases.get_approved_posts_usecase import GetApprovedPostsUseCase
from src.features.posts.user.domain.usecases.get_my_posts_usecase import GetMyPostsUseCase
from src.features.posts.user.infrastructure.validators.post_validators import CreatePostForm
from src.shared.contracts.image_storage import IImageStorage
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, PaginatedResponse, SuccessResponse, ok, paginated
from src.shared.validators.common import PaginationQuery


class PostController:
    def __init__(
        self,
        create_post: CreatePostUseCase,
        get_approved_posts: GetApprovedPostsUseCase,
        get_approved_post_by_id: GetApprovedPostByIdUseCase,
        get_my_posts: GetMyPostsUseCase,
        delete_my_post: DeleteMyPostUseCase,
        storage: IImageStorage,
    ) -> None:
        self._create_post = create_post
        self._get_approved_posts = get_approved_posts
        self._get_approved_post_by_id = get_approved_post_by_id
        self._get_my_posts = get_my_posts
        self._delete_my_post = delete_my_post
        self._storage = storage

    async def create(self, form: CreatePostForm, user: CurrentUser) -> SuccessResponse[MyPostDto]:
        post = await self._create_post.execute(
            CreatePostInput(user_id=user.id, content=form.content, image=await form.image.read())
        )
        return ok(my_post_to_dto(post, self._storage), "Publicación enviada. Se mostrará cuando el admin la apruebe.")

    async def list_approved(self, query: PaginationQuery) -> PaginatedResponse[PostDto]:
        page = await self._get_approved_posts.execute(query.to_page_request())
        return paginated([post_to_dto(post, self._storage) for post in page.items], page)

    async def get_approved(self, post_id: str) -> SuccessResponse[PostDto]:
        return ok(post_to_dto(await self._get_approved_post_by_id.execute(post_id), self._storage))

    async def list_mine(self, query: PaginationQuery, user: CurrentUser) -> PaginatedResponse[MyPostDto]:
        page = await self._get_my_posts.execute(user.id, query.to_page_request())
        return paginated([my_post_to_dto(post, self._storage) for post in page.items], page)

    async def delete_mine(self, post_id: str, user: CurrentUser) -> MessageResponse:
        await self._delete_my_post.execute(post_id, user.id)
        return MessageResponse(message="Publicación eliminada")
