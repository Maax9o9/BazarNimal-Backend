from dataclasses import dataclass

from src.core.errors.exceptions import ConflictError
from src.features.auth.domain.entities.user import NewUser, User
from src.features.auth.domain.repositories.user_repository import IUserRepository
from src.shared.contracts.password_hasher import IPasswordHasher


@dataclass(frozen=True, slots=True)
class RegisterUserInput:
    name: str
    email: str
    phone: str
    password: str


class RegisterUserUseCase:
    def __init__(self, users: IUserRepository, hasher: IPasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    async def execute(self, data: RegisterUserInput) -> User:
        email = data.email.strip().lower()
        if await self._users.exists_by_email(email):
            raise ConflictError("El correo ya está registrado")
        return await self._users.create(
            NewUser(
                name=data.name,
                email=email,
                phone=data.phone,
                password_hash=await self._hasher.hash(data.password),
            )
        )
