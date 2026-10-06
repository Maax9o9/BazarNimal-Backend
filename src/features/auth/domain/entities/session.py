from dataclasses import dataclass
from datetime import datetime

from src.features.auth.domain.entities.user import User
from src.shared.contracts.token_service import IssuedToken, OpaqueToken


@dataclass(frozen=True, slots=True)
class ClientInfo:
    ip: str | None
    user_agent: str | None


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    id: str
    user_id: str
    expires_at: datetime
    revoked_at: datetime | None

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at <= now


@dataclass(frozen=True, slots=True)
class NewRefreshToken:
    user_id: str
    token_hash: str
    expires_at: datetime
    client: ClientInfo


@dataclass(frozen=True, slots=True)
class AuthSession:
    user: User
    access_token: IssuedToken
    refresh_token: OpaqueToken


@dataclass(frozen=True, slots=True)
class LoginPolicy:
    max_failed_attempts: int
    lock_minutes: int
