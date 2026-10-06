from src.core.di.container import Container, Lifetime
from src.features.posts.user.data.repositories.post_repository_impl import PostRepositoryImpl
from src.features.posts.user.domain.repositories.post_repository import IPostRepository
from src.features.posts.user.domain.usecases.create_post_usecase import CreatePostUseCase
from src.features.posts.user.domain.usecases.delete_my_post_usecase import DeleteMyPostUseCase
from src.features.posts.user.domain.usecases.get_approved_post_by_id_usecase import GetApprovedPostByIdUseCase
from src.features.posts.user.domain.usecases.get_approved_posts_usecase import GetApprovedPostsUseCase
from src.features.posts.user.domain.usecases.get_my_posts_usecase import GetMyPostsUseCase
from src.features.posts.user.infrastructure.controllers.post_controller import PostController


def register(container: Container) -> None:
    container.register(IPostRepository, PostRepositoryImpl, lifetime=Lifetime.SCOPED)

    for usecase in (
        CreatePostUseCase,
        GetApprovedPostsUseCase,
        GetApprovedPostByIdUseCase,
        GetMyPostsUseCase,
        DeleteMyPostUseCase,
    ):
        container.register(usecase)

    container.register(PostController)
