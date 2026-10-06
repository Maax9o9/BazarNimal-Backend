from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.shared.types.current_user import CurrentUser
from src.shared.types.roles import Role


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class IssuedToken:
    value: str
    expires_in: int  # segundos


@dataclass(frozen=True, slots=True)
class OpaqueToken:
    value: str  # se entrega al cliente
    hash: str  # se guarda en la base de datos
    expires_in: int  # segundos


class ITokenService(ABC):
    @abstractmethod
    def create_access_token(self, user_id: str, role: Role) -> IssuedToken: ...

    @abstractmethod
    def verify_access_token(self, token: str) -> CurrentUser:
        """Lanza InvalidTokenError si el token no es válido o expiró."""

    @abstractmethod
    def create_refresh_token(self) -> OpaqueToken: ...

    @abstractmethod
    def hash_refresh_token(self, token: str) -> str: ...
