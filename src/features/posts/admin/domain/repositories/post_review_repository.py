from abc import ABC, abstractmethod

from src.features.posts.admin.domain.entities.post import Post, PostFilters, PostStatus
from src.shared.types.pagination import Page, PageRequest


class IPostReviewRepository(ABC):
    @abstractmethod
    async def list(self, filters: PostFilters, page: PageRequest) -> Page[Post]: ...

    @abstractmethod
    async def find_by_id(self, post_id: str) -> Post | None: ...

    @abstractmethod
    async def set_status(self, post_id: str, status: PostStatus, reviewer_id: str) -> Post: ...

    @abstractmethod
    async def soft_delete(self, post_id: str) -> None: ...
