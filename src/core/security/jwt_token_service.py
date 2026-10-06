import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from src.core.config.settings import Settings
from src.shared.contracts.token_service import (
    InvalidTokenError,
    IssuedToken,
    ITokenService,
    OpaqueToken,
)
from src.shared.types.current_user import CurrentUser
from src.shared.types.roles import Role

ALGORITHM = "HS256"
REQUIRED_CLAIMS = ["sub", "role", "iat", "exp"]


class JwtTokenService(ITokenService):
    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret.get_secret_value()
        self._ttl_by_role = {
            Role.USER: timedelta(minutes=settings.access_token_ttl_user_minutes),
            Role.ADMIN: timedelta(minutes=settings.access_token_ttl_admin_minutes),
        }
        self._refresh_ttl = timedelta(days=settings.refresh_token_ttl_days)

    def create_access_token(self, user_id: str, role: Role) -> IssuedToken:
        ttl = self._ttl_by_role[role]
        now = datetime.now(UTC)
        payload = {"sub": user_id, "role": role.value, "iat": now, "exp": now + ttl}
        token = jwt.encode(payload, self._secret, algorithm=ALGORITHM)
        return IssuedToken(value=token, expires_in=int(ttl.total_seconds()))

    def verify_access_token(self, token: str) -> CurrentUser:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": REQUIRED_CLAIMS},
            )
            return CurrentUser(id=str(payload["sub"]), role=Role(payload["role"]))
        except (jwt.PyJWTError, ValueError, KeyError) as exc:
            raise InvalidTokenError() from exc

    def create_refresh_token(self) -> OpaqueToken:
        value = secrets.token_urlsafe(48)
        return OpaqueToken(
            value=value,
            hash=self.hash_refresh_token(value),
            expires_in=int(self._refresh_ttl.total_seconds()),
        )

    def hash_refresh_token(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()
