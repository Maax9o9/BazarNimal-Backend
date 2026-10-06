from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PostStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class PostAuthor:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Post:
    id: str
    content: str
    image_url: str
    status: PostStatus
    author: PostAuthor
    reviewed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PostFilters:
    status: PostStatus | None = None
