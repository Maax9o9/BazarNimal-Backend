from src.features.posts.admin.domain.entities.post import Post, PostFilters
from src.features.posts.admin.domain.repositories.post_review_repository import IPostReviewRepository
from src.shared.types.pagination import Page, PageRequest


class GetPostsUseCase:
    def __init__(self, posts: IPostReviewRepository) -> None:
        self._posts = posts

    async def execute(self, filters: PostFilters, page: PageRequest) -> Page[Post]:
        return await self._posts.list(filters, page)
