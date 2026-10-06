from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    @abstractmethod
    async def hash(self, password: str) -> str: ...

    @abstractmethod
    async def verify(self, password_hash: str, password: str) -> bool: ...

    @abstractmethod
    def needs_rehash(self, password_hash: str) -> bool: ...
