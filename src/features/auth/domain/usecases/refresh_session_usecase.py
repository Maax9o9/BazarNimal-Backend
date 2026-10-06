from dataclasses import dataclass
from datetime import timedelta
from typing import NoReturn

from src.core.errors.exceptions import UnauthorizedError
from src.core.logger.logger import security_logger
from src.features.auth.domain.entities.session import AuthSession, ClientInfo, NewRefreshToken
from src.features.auth.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from src.features.auth.domain.repositories.user_repository import IUserRepository
from src.shared.contracts.token_service import ITokenService
from src.shared.utils.time import utcnow

INVALID_SESSION = "La sesión no es válida o expiró"


@dataclass(frozen=True, slots=True)
class RefreshSessionInput:
    refresh_token: str | None
    client: ClientInfo


class RefreshSessionUseCase:
    """Rota el refresh token: el anterior queda revocado y se emite uno nuevo."""

    def __init__(
        self,
        users: IUserRepository,
        refresh_tokens: IRefreshTokenRepository,
        tokens: ITokenService,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._tokens = tokens

    async def execute(self, data: RefreshSessionInput) -> AuthSession:
        if not data.refresh_token:
            raise UnauthorizedError(INVALID_SESSION)
        now = utcnow()
        record = await self._refresh_tokens.find_by_hash(self._tokens.hash_refresh_token(data.refresh_token))
        if record is None:
            raise UnauthorizedError(INVALID_SESSION)
        if record.revoked_at is not None:
            await self._handle_reuse(record.user_id, data.client)
        if record.is_expired(now):
            raise UnauthorizedError(INVALID_SESSION)

        user = await self._users.find_by_id(record.user_id)
        if user is None or not user.is_active:
            await self._refresh_tokens.revoke_all_for_user(record.user_id)
            raise UnauthorizedError(INVALID_SESSION)

        refresh = self._tokens.create_refresh_token()
        rotated = await self._refresh_tokens.rotate(
            record.id,
            NewRefreshToken(
                user_id=user.id,
                token_hash=refresh.hash,
                expires_at=now + timedelta(seconds=refresh.expires_in),
                client=data.client,
            ),
        )
        if not rotated:
            await self._handle_reuse(user.id, data.client)

        access = self._tokens.create_access_token(user.id, user.role)
        return AuthSession(user=user, access_token=access, refresh_token=refresh)

    async def _handle_reuse(self, user_id: str, client: ClientInfo) -> NoReturn:
        # Un refresh token ya rotado se volvió a usar: posible robo. Se cierran todas las sesiones.
        await self._refresh_tokens.revoke_all_for_user(user_id)
        security_logger.warning("refresh_token_reuse_detected", extra={"user_id": user_id, "ip": client.ip})
        raise UnauthorizedError(INVALID_SESSION)
