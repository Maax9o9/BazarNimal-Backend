from src.core.errors.exceptions import NotFoundError
from src.features.posts.user.domain.entities.post import Post
from src.features.posts.user.domain.repositories.post_repository import IPostRepository


class GetApprovedPostByIdUseCase:
    def __init__(self, posts: IPostRepository) -> None:
        self._posts = posts

    async def execute(self, post_id: str) -> Post:
        post = await self._posts.find_approved_by_id(post_id)
        if post is None:
            raise NotFoundError("La publicación no existe")
        return post
