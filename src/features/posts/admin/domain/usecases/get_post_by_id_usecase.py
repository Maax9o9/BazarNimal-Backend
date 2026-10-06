from src.core.errors.exceptions import NotFoundError
from src.features.posts.admin.domain.entities.post import Post
from src.features.posts.admin.domain.repositories.post_review_repository import IPostReviewRepository


class GetPostByIdUseCase:
    def __init__(self, posts: IPostReviewRepository) -> None:
        self._posts = posts

    async def execute(self, post_id: str) -> Post:
        post = await self._posts.find_by_id(post_id)
        if post is None:
            raise NotFoundError("La publicación no existe")
        return post
