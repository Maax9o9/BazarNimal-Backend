from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors.exceptions import NotFoundError
from src.features.posts.admin.data.mappers.post_admin_mapper import row_to_post
from src.features.posts.admin.data.models.post_review_tables import posts, users
from src.features.posts.admin.domain.entities.post import Post, PostFilters, PostStatus
from src.features.posts.admin.domain.repositories.post_review_repository import IPostReviewRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.query import fetch_page
from src.shared.utils.time import utcnow


def _base_query() -> Select:
    return (
        select(
            posts.c.id,
            posts.c.content,
            posts.c.image_url,
            posts.c.status,
            posts.c.reviewed_at,
            posts.c.created_at,
            users.c.id.label("author_id"),
            users.c.name.label("author_name"),
        )
        .join(users, users.c.id == posts.c.user_id)
        .where(posts.c.deleted_at.is_(None))
    )


class PostReviewRepositoryImpl(IPostReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, filters: PostFilters, page: PageRequest) -> Page[Post]:
        query = _base_query()
        if filters.status:
            query = query.where(posts.c.status == filters.status.value)
        # Las más antiguas primero: el admin revisa en orden de llegada.
        order = [posts.c.created_at.asc(), posts.c.id]
        return await fetch_page(self._session, query, order, page, row_to_post)

    async def find_by_id(self, post_id: str) -> Post | None:
        row = (await self._session.execute(_base_query().where(posts.c.id == post_id))).mappings().first()
        return row_to_post(row) if row else None

    async def set_status(self, post_id: str, status: PostStatus, reviewer_id: str) -> Post:
        now = utcnow()
        await self._session.execute(
            update(posts)
            .where(posts.c.id == post_id, posts.c.deleted_at.is_(None))
            .values(status=status.value, reviewed_by=reviewer_id, reviewed_at=now, updated_at=now)
        )
        await self._session.commit()
        post = await self.find_by_id(post_id)
        if post is None:
            raise NotFoundError("La publicación no existe")
        return post

    async def soft_delete(self, post_id: str) -> None:
        now = utcnow()
        await self._session.execute(update(posts).where(posts.c.id == post_id).values(deleted_at=now, updated_at=now))
        await self._session.commit()
