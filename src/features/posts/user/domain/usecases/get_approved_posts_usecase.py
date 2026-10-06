from src.features.posts.user.domain.entities.post import Post
from src.features.posts.user.domain.repositories.post_repository import IPostRepository
from src.shared.types.pagination import Page, PageRequest


class GetApprovedPostsUseCase:
    def __init__(self, posts: IPostRepository) -> None:
        self._posts = posts

    async def execute(self, page: PageRequest) -> Page[Post]:
        return await self._posts.list_approved(page)
