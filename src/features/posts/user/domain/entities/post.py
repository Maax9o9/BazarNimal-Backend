from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PostStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class Post:
    id: str
    content: str
    image_url: str
    author_name: str
    status: PostStatus
    created_at: datetime


@dataclass(frozen=True, slots=True)
class OwnedPost:
    id: str
    user_id: str
    image_url: str
