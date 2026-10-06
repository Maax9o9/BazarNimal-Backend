"""Repositorios y servicios en memoria para probar casos de uso sin base de datos."""

from dataclasses import replace
from datetime import datetime

from src.features.adoptions.admin.domain.entities.adoption_request import (
    AdoptionRequest,
    AdoptionRequestFilters,
    AdoptionRequestStatus,
)
from src.features.adoptions.admin.domain.entities.pet import PetStatus
from src.features.adoptions.admin.domain.repositories.adoption_request_repository import IAdoptionRequestRepository
from src.features.auth.domain.entities.session import NewRefreshToken, RefreshTokenRecord
from src.features.auth.domain.entities.user import NewUser, User
from src.features.auth.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from src.features.auth.domain.repositories.user_repository import IUserRepository
from src.shared.contracts.image_storage import IImageStorage
from src.shared.contracts.password_hasher import IPasswordHasher
from src.shared.types.pagination import Page, PageRequest
from src.shared.utils.ids import new_id
from src.shared.utils.time import utcnow


class FakePasswordHasher(IPasswordHasher):
    async def hash(self, password: str) -> str:
        return f"hashed:{password}"

    async def verify(self, password_hash: str, password: str) -> bool:
        return password_hash == f"hashed:{password}"

    def needs_rehash(self, password_hash: str) -> bool:
        return False


class InMemoryUserRepository(IUserRepository):
    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    async def find_by_email(self, email: str) -> User | None:
        return next((u for u in self.users.values() if u.email == email), None)

    async def find_by_id(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    async def exists_by_email(self, email: str) -> bool:
        return await self.find_by_email(email) is not None

    async def create(self, data: NewUser) -> User:
        user = User(
            id=new_id(),
            name=data.name,
            email=data.email,
            phone=data.phone,
            role=data.role,
            is_active=True,
            password_hash=data.password_hash,
            failed_login_attempts=0,
            locked_until=None,
            created_at=utcnow(),
        )
        self.users[user.id] = user
        return user

    async def record_failed_login(self, user_id: str, attempts: int, locked_until: datetime | None) -> None:
        user = self.users[user_id]
        user.failed_login_attempts = attempts
        user.locked_until = locked_until

    async def reset_failed_logins(self, user_id: str) -> None:
        await self.record_failed_login(user_id, 0, None)

    async def update_password_hash(self, user_id: str, password_hash: str) -> None:
        self.users[user_id].password_hash = password_hash


class InMemoryRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self) -> None:
        self.tokens: dict[str, tuple[str, RefreshTokenRecord]] = {}  # id -> (hash, record)

    async def create(self, data: NewRefreshToken) -> str:
        token_id = new_id()
        self.tokens[token_id] = (
            data.token_hash,
            RefreshTokenRecord(id=token_id, user_id=data.user_id, expires_at=data.expires_at, revoked_at=None),
        )
        return token_id

    async def find_by_hash(self, token_hash: str) -> RefreshTokenRecord | None:
        return next((record for h, record in self.tokens.values() if h == token_hash), None)

    async def rotate(self, current_id: str, replacement: NewRefreshToken) -> bool:
        token_hash, record = self.tokens[current_id]
        if record.revoked_at is not None:
            return False
        await self.revoke(current_id)
        await self.create(replacement)
        return True

    async def revoke(self, token_id: str) -> None:
        token_hash, record = self.tokens[token_id]
        self.tokens[token_id] = (token_hash, replace(record, revoked_at=utcnow()))

    async def revoke_all_for_user(self, user_id: str) -> None:
        for token_id, (_, record) in list(self.tokens.items()):
            if record.user_id == user_id and record.revoked_at is None:
                await self.revoke(token_id)


class InMemoryAdoptionRequestRepository(IAdoptionRequestRepository):
    def __init__(self, requests: list[AdoptionRequest]) -> None:
        self.requests = {request.id: request for request in requests}
        self.approved: list[str] = []

    async def list(self, filters: AdoptionRequestFilters, page: PageRequest) -> Page[AdoptionRequest]:
        items = list(self.requests.values())
        return Page(items=items, total=len(items), page=page.page, limit=page.limit)

    async def find_by_id(self, request_id: str) -> AdoptionRequest | None:
        return self.requests.get(request_id)

    async def approve(self, request_id: str, pet_id: str, reviewer_id: str) -> None:
        self.approved.append(request_id)
        for key, request in self.requests.items():
            if request.pet_id != pet_id:
                continue
            status = AdoptionRequestStatus.APPROVED if key == request_id else AdoptionRequestStatus.REJECTED
            self.requests[key] = replace(request, status=status, pet_status=PetStatus.ADOPTED)

    async def reject(self, request_id: str, reviewer_id: str) -> None:
        self.requests[request_id] = replace(self.requests[request_id], status=AdoptionRequestStatus.REJECTED)


class FakeImageStorage(IImageStorage):
    def __init__(self) -> None:
        self.saved: list[str] = []
        self.deleted: list[str] = []

    async def save(self, content: bytes, folder: str) -> str:
        url = f"/uploads/images/{folder}/{new_id()}.webp"
        self.saved.append(url)
        return url

    async def delete(self, relative_url: str | None) -> None:
        if relative_url:
            self.deleted.append(relative_url)

    def public_url(self, relative_url: str | None) -> str | None:
        return relative_url
