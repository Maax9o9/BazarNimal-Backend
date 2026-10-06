from dataclasses import dataclass

from src.features.posts.user.domain.entities.post import Post
from src.features.posts.user.domain.repositories.post_repository import IPostRepository
from src.shared.contracts.image_storage import IImageStorage

IMAGE_FOLDER = "posts"


@dataclass(frozen=True, slots=True)
class CreatePostInput:
    user_id: str
    content: str
    image: bytes


class CreatePostUseCase:
    """La publicación nace como pendiente: solo se muestra cuando el admin la aprueba."""

    def __init__(self, posts: IPostRepository, storage: IImageStorage) -> None:
        self._posts = posts
        self._storage = storage

    async def execute(self, data: CreatePostInput) -> Post:
        image_url = await self._storage.save(data.image, IMAGE_FOLDER)
        try:
            return await self._posts.create(data.user_id, data.content, image_url)
        except Exception:
            await self._storage.delete(image_url)
            raise
