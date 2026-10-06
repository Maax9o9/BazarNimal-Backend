from abc import ABC, abstractmethod
from datetime import datetime

from src.features.auth.domain.entities.user import NewUser, User


class IUserRepository(ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    async def create(self, data: NewUser) -> User: ...

    @abstractmethod
    async def record_failed_login(self, user_id: str, attempts: int, locked_until: datetime | None) -> None: ...

    @abstractmethod
    async def reset_failed_logins(self, user_id: str) -> None: ...

    @abstractmethod
    async def update_password_hash(self, user_id: str, password_hash: str) -> None: ...
