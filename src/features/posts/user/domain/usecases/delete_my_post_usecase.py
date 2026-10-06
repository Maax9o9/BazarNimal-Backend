from src.core.errors.exceptions import NotFoundError
from src.features.posts.user.domain.repositories.post_repository import IPostRepository
from src.shared.contracts.image_storage import IImageStorage


class DeleteMyPostUseCase:
    def __init__(self, posts: IPostRepository, storage: IImageStorage) -> None:
        self._posts = posts
        self._storage = storage

    async def execute(self, post_id: str, user_id: str) -> None:
        # 404 tanto si no existe como si es de otro usuario: no se revela que exista.
        post = await self._posts.find_owned(post_id, user_id)
        if post is None:
            raise NotFoundError("La publicación no existe")
        await self._posts.soft_delete(post.id)
        await self._storage.delete(post.image_url)
