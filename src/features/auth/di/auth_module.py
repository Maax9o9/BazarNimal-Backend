from src.core.config.settings import Settings
from src.core.di.container import Container, Lifetime
from src.features.auth.data.mappers.user_mapper import UserMapper
from src.features.auth.data.repositories.refresh_token_repository_impl import RefreshTokenRepositoryImpl
from src.features.auth.data.repositories.user_repository_impl import UserRepositoryImpl
from src.features.auth.domain.entities.session import LoginPolicy
from src.features.auth.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from src.features.auth.domain.repositories.user_repository import IUserRepository
from src.features.auth.domain.usecases.get_current_user_usecase import GetCurrentUserUseCase
from src.features.auth.domain.usecases.login_usecase import LoginUseCase
from src.features.auth.domain.usecases.logout_usecase import LogoutUseCase
from src.features.auth.domain.usecases.refresh_session_usecase import RefreshSessionUseCase
from src.features.auth.domain.usecases.register_user_usecase import RegisterUserUseCase
from src.features.auth.infrastructure.controllers.auth_controller import AuthController


def _login_policy(settings: Settings) -> LoginPolicy:
    return LoginPolicy(
        max_failed_attempts=settings.login_max_failed_attempts,
        lock_minutes=settings.login_lock_minutes,
    )


def register(container: Container) -> None:
    container.register(LoginPolicy, _login_policy, lifetime=Lifetime.SINGLETON)
    container.register(UserMapper, lifetime=Lifetime.SINGLETON)
    container.register(IUserRepository, UserRepositoryImpl, lifetime=Lifetime.SCOPED)
    container.register(IRefreshTokenRepository, RefreshTokenRepositoryImpl, lifetime=Lifetime.SCOPED)

    container.register(RegisterUserUseCase)
    container.register(LoginUseCase)
    container.register(RefreshSessionUseCase)
    container.register(LogoutUseCase)
    container.register(GetCurrentUserUseCase)
    container.register(AuthController)
