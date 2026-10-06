from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.posts.user.data.mappers.post_mapper import row_to_post
from src.features.posts.user.data.models.post_tables import posts, users
from src.features.posts.user.domain.entities.post import OwnedPost, Post
from src.features.posts.user.domain.repositories.post_repository import IPostRepository
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.ids import new_id
from src.shared.utils.query import fetch_page
from src.shared.utils.time import utcnow

NEWEST_FIRST = [posts.c.created_at.desc(), posts.c.id]


def _base_query() -> Select:
    return (
        select(
            posts.c.id,
            posts.c.content,
            posts.c.image_url,
            posts.c.status,
            posts.c.created_at,
            users.c.name.label("author_name"),
        )
        .join(users, users.c.id == posts.c.user_id)
        .where(posts.c.deleted_at.is_(None))
    )


class PostRepositoryImpl(IPostRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: str, content: str, image_url: str) -> Post:
        now = utcnow()
        post_id = new_id()
        await self._session.execute(
            posts.insert().values(
                id=post_id,
                user_id=user_id,
                content=content,
                image_url=image_url,
                status="pending",
                created_at=now,
                updated_at=now,
            )
        )
        await self._session.commit()
        row = (await self._session.execute(_base_query().where(posts.c.id == post_id))).mappings().one()
        return row_to_post(row)

    async def list_approved(self, page: PageRequest) -> Page[Post]:
        query = _base_query().where(posts.c.status == "approved")
        return await fetch_page(self._session, query, NEWEST_FIRST, page, row_to_post)

    async def find_approved_by_id(self, post_id: str) -> Post | None:
        query = _base_query().where(posts.c.id == post_id, posts.c.status == "approved")
        row = (await self._session.execute(query)).mappings().first()
        return row_to_post(row) if row else None

    async def list_by_user(self, user_id: str, page: PageRequest) -> Page[Post]:
        query = _base_query().where(posts.c.user_id == user_id)
        return await fetch_page(self._session, query, NEWEST_FIRST, page, row_to_post)

    async def find_owned(self, post_id: str, user_id: str) -> OwnedPost | None:
        query = select(posts.c.id, posts.c.user_id, posts.c.image_url).where(
            posts.c.id == post_id,
            posts.c.user_id == user_id,
            posts.c.deleted_at.is_(None),
        )
        row = (await self._session.execute(query)).mappings().first()
        return OwnedPost(id=row["id"], user_id=row["user_id"], image_url=row["image_url"]) if row else None

    async def soft_delete(self, post_id: str) -> None:
        now = utcnow()
        await self._session.execute(update(posts).where(posts.c.id == post_id).values(deleted_at=now, updated_at=now))
        await self._session.commit()
