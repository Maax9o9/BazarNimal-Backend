from datetime import datetime

from pydantic import BaseModel

from src.features.posts.user.domain.entities.post import PostStatus


class PostDto(BaseModel):
    id: str
    content: str
    image_url: str | None
    author_name: str
    created_at: datetime


class MyPostDto(PostDto):
    status: PostStatus
