from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageRequest:
    page: int = 1
    limit: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    total: int
    page: int
    limit: int
