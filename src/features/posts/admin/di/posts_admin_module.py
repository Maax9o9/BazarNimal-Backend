from src.core.di.container import Container, Lifetime
from src.features.posts.admin.data.repositories.post_review_repository_impl import PostReviewRepositoryImpl
from src.features.posts.admin.domain.repositories.post_review_repository import IPostReviewRepository
from src.features.posts.admin.domain.usecases.approve_post_usecase import ApprovePostUseCase
from src.features.posts.admin.domain.usecases.delete_post_usecase import DeletePostUseCase
from src.features.posts.admin.domain.usecases.get_post_by_id_usecase import GetPostByIdUseCase
from src.features.posts.admin.domain.usecases.get_posts_usecase import GetPostsUseCase
from src.features.posts.admin.domain.usecases.reject_post_usecase import RejectPostUseCase
from src.features.posts.admin.infrastructure.controllers.post_admin_controller import PostAdminController


def register(container: Container) -> None:
    container.register(IPostReviewRepository, PostReviewRepositoryImpl, lifetime=Lifetime.SCOPED)

    for usecase in (GetPostsUseCase, GetPostByIdUseCase, ApprovePostUseCase, RejectPostUseCase, DeletePostUseCase):
        container.register(usecase)

    container.register(PostAdminController)
