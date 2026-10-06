from sqlalchemy import RowMapping

from src.features.posts.user.data.dtos.post_dtos import MyPostDto, PostDto
from src.features.posts.user.domain.entities.post import Post, PostStatus
from src.shared.contracts.image_storage import IImageStorage


def row_to_post(row: RowMapping) -> Post:
    return Post(
        id=row["id"],
        content=row["content"],
        image_url=row["image_url"],
        author_name=row["author_name"],
        status=PostStatus(row["status"]),
        created_at=row["created_at"],
    )


def post_to_dto(post: Post, storage: IImageStorage) -> PostDto:
    return PostDto(
        id=post.id,
        content=post.content,
        image_url=storage.public_url(post.image_url),
        author_name=post.author_name,
        created_at=post.created_at,
    )


def my_post_to_dto(post: Post, storage: IImageStorage) -> MyPostDto:
    return MyPostDto(**post_to_dto(post, storage).model_dump(), status=post.status)
