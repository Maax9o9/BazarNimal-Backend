
from collections.abc import Awaitable, Callable

from fastapi import Depends

from src.core.errors.exceptions import ForbiddenError
from src.shared.middlewares.authenticate import authenticate
from src.shared.types.current_user import CurrentUser
from src.shared.types.roles import Role


def authorize(*roles: Role) -> Callable[..., Awaitable[CurrentUser]]:
    allowed = set(roles)

    async def dependency(user: CurrentUser = Depends(authenticate)) -> CurrentUser:
        if user.role not in allowed:
            raise ForbiddenError("No tienes permisos para realizar esta acción")
        return user

    return dependency


require_admin = authorize(Role.ADMIN)
require_user = authorize(Role.USER)
