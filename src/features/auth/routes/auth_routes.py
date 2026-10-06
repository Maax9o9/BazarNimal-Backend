from fastapi import APIRouter, Depends, Request, Response, status

from src.core.di.fastapi import inject
from src.features.auth.data.dtos.auth_dtos import SessionDto, UserDto
from src.features.auth.infrastructure.controllers.auth_controller import AuthController
from src.features.auth.infrastructure.validators.auth_validators import LoginRequest, RegisterRequest
from src.shared.middlewares.authenticate import authenticate
from src.shared.middlewares.rate_limit import by_body_email, by_ip, rate_limit
from src.shared.types.current_user import CurrentUser
from src.shared.utils.responses import MessageResponse, SuccessResponse, errors

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario",
    responses=errors(409, 422, 429),
    dependencies=[Depends(rate_limit("register", by_ip))],
)
async def register(
    body: RegisterRequest,
    controller: AuthController = inject(AuthController),
) -> SuccessResponse[UserDto]:
    return await controller.register(body)


@router.post(
    "/login",
    summary="Inicio de sesión (emite cookies HttpOnly)",
    description=(
        "Devuelve el rol del usuario para que el frontend redirija a la vista de **user** o **admin**. "
        "El access token dura 15 minutos para user y 2 horas para admin."
    ),
    responses=errors(401, 422, 429),
    dependencies=[Depends(rate_limit("login", by_ip, by_body_email))],
)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    controller: AuthController = inject(AuthController),
) -> SuccessResponse[SessionDto]:
    return await controller.login(body, request, response)


@router.post(
    "/refresh",
    summary="Rotación del refresh token",
    responses=errors(401, 429),
    dependencies=[Depends(rate_limit("login", by_ip))],
)
async def refresh(
    request: Request,
    response: Response,
    controller: AuthController = inject(AuthController),
) -> SuccessResponse[SessionDto]:
    return await controller.refresh(request, response)


@router.post("/logout", summary="Cierre de sesión y revocación del refresh token")
async def logout(
    request: Request,
    response: Response,
    controller: AuthController = inject(AuthController),
) -> MessageResponse:
    return await controller.logout(request, response)


@router.get("/me", summary="Datos del usuario autenticado", responses=errors(401))
async def me(
    user: CurrentUser = Depends(authenticate),
    controller: AuthController = inject(AuthController),
) -> SuccessResponse[UserDto]:
    return await controller.me(user)
