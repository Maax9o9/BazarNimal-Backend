from datetime import datetime

from pydantic import BaseModel

from src.features.posts.admin.domain.entities.post import PostStatus


class PostAuthorDto(BaseModel):
    id: str
    name: str


class PostAdminDto(BaseModel):
    id: str
    content: str
    image_url: str | None
    status: PostStatus
    author: PostAuthorDto
    reviewed_at: datetime | None
    created_at: datetime
