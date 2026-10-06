from abc import ABC, abstractmethod

from src.features.auth.domain.entities.session import NewRefreshToken, RefreshTokenRecord


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def create(self, data: NewRefreshToken) -> str: ...

    @abstractmethod
    async def find_by_hash(self, token_hash: str) -> RefreshTokenRecord | None: ...

    @abstractmethod
    async def rotate(self, current_id: str, replacement: NewRefreshToken) -> bool:
        """Revoca el token actual y crea el nuevo en una transacción.

        Devuelve False si el token actual ya estaba revocado (reutilización).
        """

    @abstractmethod
    async def revoke(self, token_id: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None: ...
