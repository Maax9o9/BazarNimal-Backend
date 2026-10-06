from fastapi import Request, Response

from src.core.security.cookies import REFRESH_COOKIE, CookieManager
from src.features.auth.data.dtos.auth_dtos import SessionDto, UserDto
from src.features.auth.data.mappers.user_mapper import session_to_dto, user_to_dto
from src.features.auth.domain.entities.session import AuthSession, ClientInfo
from src.features.auth.domain.usecases.get_current_user_usecase import GetCurrentUserUseCase
from src.features.auth.domain.usecases.login_usecase import LoginInput, LoginUseCase
from src.features.auth.domain.usecases.logout_usecase import LogoutUseCase
from src.features.auth.domain.usecases.refresh_session_usecase import RefreshSessionInput, RefreshSessionUseCase
from src.features.auth.domain.usecases.register_user_usecase import RegisterUserInput, RegisterUserUseCase
from src.features.auth.infrastructure.validators.auth_validators import LoginRequest, RegisterRequest
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, SuccessResponse, ok


def _client(request: Request) -> ClientInfo:
    return ClientInfo(
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


class AuthController:
    def __init__(
        self,
        register_user: RegisterUserUseCase,
        login: LoginUseCase,
        refresh_session: RefreshSessionUseCase,
        logout: LogoutUseCase,
        get_current_user: GetCurrentUserUseCase,
        cookies: CookieManager,
    ) -> None:
        self._register_user = register_user
        self._login = login
        self._refresh_session = refresh_session
        self._logout = logout
        self._get_current_user = get_current_user
        self._cookies = cookies

    async def register(self, body: RegisterRequest) -> SuccessResponse[UserDto]:
        user = await self._register_user.execute(
            RegisterUserInput(name=body.name, email=body.email, phone=body.phone, password=body.password)
        )
        return ok(user_to_dto(user), "Registro exitoso. Ya puedes iniciar sesión.")

    async def login(self, body: LoginRequest, request: Request, response: Response) -> SuccessResponse[SessionDto]:
        session = await self._login.execute(
            LoginInput(email=body.email, password=body.password, client=_client(request))
        )
        self._set_cookies(response, session)
        return ok(session_to_dto(session), "Sesión iniciada")

    async def refresh(self, request: Request, response: Response) -> SuccessResponse[SessionDto]:
        session = await self._refresh_session.execute(
            RefreshSessionInput(refresh_token=request.cookies.get(REFRESH_COOKIE), client=_client(request))
        )
        self._set_cookies(response, session)
        return ok(session_to_dto(session), "Sesión renovada")

    async def logout(self, request: Request, response: Response) -> MessageResponse:
        await self._logout.execute(request.cookies.get(REFRESH_COOKIE))
        self._cookies.clear_session(response)
        return MessageResponse(message="Sesión cerrada")

    async def me(self, user: CurrentUser) -> SuccessResponse[UserDto]:
        return ok(user_to_dto(await self._get_current_user.execute(user.id)))

    def _set_cookies(self, response: Response, session: AuthSession) -> None:
        self._cookies.set_session(
            response,
            access_token=session.access_token.value,
            access_expires_in=session.access_token.expires_in,
            refresh_token=session.refresh_token.value,
            refresh_expires_in=session.refresh_token.expires_in,
        )
