from sqlalchemy import RowMapping

from src.features.posts.admin.data.dtos.post_admin_dtos import PostAdminDto, PostAuthorDto
from src.features.posts.admin.domain.entities.post import Post, PostAuthor, PostStatus
from src.shared.contracts.image_storage import IImageStorage


def row_to_post(row: RowMapping) -> Post:
    return Post(
        id=row["id"],
        content=row["content"],
        image_url=row["image_url"],
        status=PostStatus(row["status"]),
        author=PostAuthor(id=row["author_id"], name=row["author_name"]),
        reviewed_at=row["reviewed_at"],
        created_at=row["created_at"],
    )


def post_to_dto(post: Post, storage: IImageStorage) -> PostAdminDto:
    return PostAdminDto(
        id=post.id,
        content=post.content,
        image_url=storage.public_url(post.image_url),
        status=post.status,
        author=PostAuthorDto(id=post.author.id, name=post.author.name),
        reviewed_at=post.reviewed_at,
        created_at=post.created_at,
    )
