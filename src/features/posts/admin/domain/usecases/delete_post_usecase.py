from src.core.errors.exceptions import NotFoundError
from src.features.posts.admin.domain.repositories.post_review_repository import IPostReviewRepository
from src.shared.contracts.image_storage import IImageStorage


class DeletePostUseCase:
    def __init__(self, posts: IPostReviewRepository, storage: IImageStorage) -> None:
        self._posts = posts
        self._storage = storage

    async def execute(self, post_id: str) -> None:
        post = await self._posts.find_by_id(post_id)
        if post is None:
            raise NotFoundError("La publicación no existe")
        await self._posts.soft_delete(post_id)
        await self._storage.delete(post.image_url)
