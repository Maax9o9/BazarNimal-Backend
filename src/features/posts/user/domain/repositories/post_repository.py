from abc import ABC, abstractmethod

from src.features.posts.user.domain.entities.post import OwnedPost, Post
from src.shared.types.pagination import Page, PageRequest


class IPostRepository(ABC):
    @abstractmethod
    async def create(self, user_id: str, content: str, image_url: str) -> Post: ...

    @abstractmethod
    async def list_approved(self, page: PageRequest) -> Page[Post]: ...

    @abstractmethod
    async def find_approved_by_id(self, post_id: str) -> Post | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: str, page: PageRequest) -> Page[Post]: ...

    @abstractmethod
    async def find_owned(self, post_id: str, user_id: str) -> OwnedPost | None:
        """Solo devuelve la publicación si pertenece al usuario (prevención de IDOR)."""

    @abstractmethod
    async def soft_delete(self, post_id: str) -> None: ...
