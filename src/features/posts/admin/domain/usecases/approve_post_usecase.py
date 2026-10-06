from src.core.errors.exceptions import ConflictError, NotFoundError
from src.features.posts.admin.domain.entities.post import Post, PostStatus
from src.features.posts.admin.domain.repositories.post_review_repository import IPostReviewRepository


class ApprovePostUseCase:
    """Aprobada = visible en la página. También permite aprobar una publicación rechazada antes."""

    def __init__(self, posts: IPostReviewRepository) -> None:
        self._posts = posts

    async def execute(self, post_id: str, admin_id: str) -> Post:
        post = await self._posts.find_by_id(post_id)
        if post is None:
            raise NotFoundError("La publicación no existe")
        if post.status is PostStatus.APPROVED:
            raise ConflictError("La publicación ya está aprobada")
        return await self._posts.set_status(post_id, PostStatus.APPROVED, admin_id)
