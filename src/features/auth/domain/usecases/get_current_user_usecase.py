from src.core.errors.exceptions import UnauthorizedError
from src.features.auth.domain.entities.user import User
from src.features.auth.domain.repositories.user_repository import IUserRepository


class GetCurrentUserUseCase:
    def __init__(self, users: IUserRepository) -> None:
        self._users = users

    async def execute(self, user_id: str) -> User:
        user = await self._users.find_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("La sesión no es válida o expiró")
        return user
