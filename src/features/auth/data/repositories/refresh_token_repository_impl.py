from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.features.auth.data.models.auth_tables import refresh_tokens
from src.features.auth.domain.entities.session import NewRefreshToken, RefreshTokenRecord
from src.features.auth.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from src.shared.utils.ids import new_id
from src.shared.utils.time import utcnow


class RefreshTokenRepositoryImpl(IRefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: NewRefreshToken) -> str:
        token_id = await self._insert(data)
        await self._session.commit()
        return token_id

    async def find_by_hash(self, token_hash: str) -> RefreshTokenRecord | None:
        query = select(
            refresh_tokens.c.id,
            refresh_tokens.c.user_id,
            refresh_tokens.c.expires_at,
            refresh_tokens.c.revoked_at,
        ).where(refresh_tokens.c.token_hash == token_hash)
        row = (await self._session.execute(query)).mappings().first()
        if row is None:
            return None
        return RefreshTokenRecord(
            id=row["id"],
            user_id=row["user_id"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )

    async def rotate(self, current_id: str, replacement: NewRefreshToken) -> bool:
        try:
            new_token_id = await self._insert(replacement)
            result = await self._session.execute(
                update(refresh_tokens)
                .where(refresh_tokens.c.id == current_id, refresh_tokens.c.revoked_at.is_(None))
                .values(revoked_at=utcnow(), replaced_by=new_token_id)
            )
            if result.rowcount != 1:
                await self._session.rollback()
                return False
            await self._session.commit()
            return True
        except Exception:
            await self._session.rollback()
            raise

    async def revoke(self, token_id: str) -> None:
        await self._session.execute(
            update(refresh_tokens)
            .where(refresh_tokens.c.id == token_id, refresh_tokens.c.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        await self._session.commit()

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._session.execute(
            update(refresh_tokens)
            .where(refresh_tokens.c.user_id == user_id, refresh_tokens.c.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        await self._session.commit()

    async def _insert(self, data: NewRefreshToken) -> str:
        token_id = new_id()
        await self._session.execute(
            refresh_tokens.insert().values(
                id=token_id,
                user_id=data.user_id,
                token_hash=data.token_hash,
                expires_at=data.expires_at,
                created_by_ip=data.client.ip,
                user_agent=(data.client.user_agent or "")[:255] or None,
                created_at=utcnow(),
            )
        )
        return token_id
