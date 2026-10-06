"""`authenticate`: verifica el JWT de la cookie access_token."""

from fastapi import Request, Security
from fastapi.security import APIKeyCookie

from src.core.di.fastapi import inject
from src.core.errors.exceptions import UnauthorizedError
from src.core.security.cookies import ACCESS_COOKIE
from src.shared.contracts.token_service import InvalidTokenError, ITokenService
from src.shared.types.current_user import CurrentUser

access_token_cookie = APIKeyCookie(
    name=ACCESS_COOKIE,
    auto_error=False,
    description="Cookie HttpOnly emitida por POST /api/v1/auth/login",
)


async def authenticate(
    request: Request,
    token: str | None = Security(access_token_cookie),
    token_service: ITokenService = inject(ITokenService),
) -> CurrentUser:
    if not token:
        raise UnauthorizedError("No has iniciado sesión")
    try:
        user = token_service.verify_access_token(token)
    except InvalidTokenError:
        raise UnauthorizedError("La sesión no es válida o expiró") from None
    request.state.user = user
    return user
