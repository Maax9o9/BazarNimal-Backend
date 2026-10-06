from pydantic import Field

from src.features.posts.admin.domain.entities.post import PostFilters, PostStatus
from src.shared.validators.common import PaginationQuery


class PostListQuery(PaginationQuery):
    status: PostStatus | None = Field(
        default=None, description="pending = pendiente, approved = aceptada, rejected = rechazada"
    )

    def to_filters(self) -> PostFilters:
        return PostFilters(status=self.status)
