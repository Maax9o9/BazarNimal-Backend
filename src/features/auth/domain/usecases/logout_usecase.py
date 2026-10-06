from src.features.auth.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from src.shared.contracts.token_service import ITokenService


class LogoutUseCase:
    def __init__(self, refresh_tokens: IRefreshTokenRepository, tokens: ITokenService) -> None:
        self._refresh_tokens = refresh_tokens
        self._tokens = tokens

    async def execute(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        record = await self._refresh_tokens.find_by_hash(self._tokens.hash_refresh_token(refresh_token))
        if record is not None and record.revoked_at is None:
            await self._refresh_tokens.revoke(record.id)
