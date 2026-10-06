from dataclasses import dataclass
from datetime import timedelta

from src.core.errors.exceptions import TooManyRequestsError, UnauthorizedError
from src.core.logger.logger import security_logger
from src.features.auth.domain.entities.session import AuthSession, ClientInfo, LoginPolicy, NewRefreshToken
from src.features.auth.domain.entities.user import User
from src.features.auth.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from src.features.auth.domain.repositories.user_repository import IUserRepository
from src.shared.contracts.password_hasher import IPasswordHasher
from src.shared.contracts.token_service import ITokenService
from src.shared.utils.time import utcnow

INVALID_CREDENTIALS = "Credenciales inválidas"


@dataclass(frozen=True, slots=True)
class LoginInput:
    email: str
    password: str
    client: ClientInfo


class LoginUseCase:
    _dummy_hash: str | None = None

    def __init__(
        self,
        users: IUserRepository,
        refresh_tokens: IRefreshTokenRepository,
        hasher: IPasswordHasher,
        tokens: ITokenService,
        policy: LoginPolicy,
    ) -> None:
        self._users = users
        self._refresh_tokens = refresh_tokens
        self._hasher = hasher
        self._tokens = tokens
        self._policy = policy

    async def execute(self, data: LoginInput) -> AuthSession:
        now = utcnow()
        user = await self._users.find_by_email(data.email.strip().lower())

        if user is None or not user.is_active:
            # Mismo costo que una verificación real para no revelar si el correo existe.
            await self._hasher.verify(await self._get_dummy_hash(), data.password)
            self._log_failure("unknown_or_inactive_user", data.client)
            raise UnauthorizedError(INVALID_CREDENTIALS)

        if user.locked_until is not None and user.locked_until > now:
            self._log_failure("account_locked", data.client, user.id)
            retry_after = max(1, int((user.locked_until - now).total_seconds()))
            raise TooManyRequestsError(
                "Demasiados intentos fallidos. Intenta de nuevo más tarde.",
                headers={"Retry-After": str(retry_after)},
            )

        if not await self._hasher.verify(user.password_hash, data.password):
            await self._register_failure(user, data.client)
            raise UnauthorizedError(INVALID_CREDENTIALS)

        if user.failed_login_attempts or user.locked_until:
            await self._users.reset_failed_logins(user.id)
        if self._hasher.needs_rehash(user.password_hash):
            await self._users.update_password_hash(user.id, await self._hasher.hash(data.password))

        access = self._tokens.create_access_token(user.id, user.role)
        refresh = self._tokens.create_refresh_token()
        await self._refresh_tokens.create(
            NewRefreshToken(
                user_id=user.id,
                token_hash=refresh.hash,
                expires_at=now + timedelta(seconds=refresh.expires_in),
                client=data.client,
            )
        )
        security_logger.info("login_succeeded", extra={"user_id": user.id, "ip": data.client.ip})
        return AuthSession(user=user, access_token=access, refresh_token=refresh)

    async def _register_failure(self, user: User, client: ClientInfo) -> None:
        attempts = user.failed_login_attempts + 1
        if attempts >= self._policy.max_failed_attempts:
            locked_until = utcnow() + timedelta(minutes=self._policy.lock_minutes)
            await self._users.record_failed_login(user.id, 0, locked_until)
            self._log_failure("account_locked_now", client, user.id)
        else:
            await self._users.record_failed_login(user.id, attempts, None)
            self._log_failure("wrong_password", client, user.id)

    async def _get_dummy_hash(self) -> str:
        if LoginUseCase._dummy_hash is None:
            LoginUseCase._dummy_hash = await self._hasher.hash("dummy-password-for-timing")
        return LoginUseCase._dummy_hash

    @staticmethod
    def _log_failure(reason: str, client: ClientInfo, user_id: str | None = None) -> None:
        security_logger.warning("login_failed", extra={"reason": reason, "user_id": user_id, "ip": client.ip})
