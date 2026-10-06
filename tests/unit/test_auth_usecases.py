from datetime import timedelta

import pytest

from src.core.config.settings import Settings
from src.core.errors.exceptions import ConflictError, TooManyRequestsError, UnauthorizedError
from src.core.security.jwt_token_service import JwtTokenService
from src.features.auth.domain.entities.session import ClientInfo, LoginPolicy
from src.features.auth.domain.usecases.login_usecase import LoginInput, LoginUseCase
from src.features.auth.domain.usecases.refresh_session_usecase import RefreshSessionInput, RefreshSessionUseCase
from src.features.auth.domain.usecases.register_user_usecase import RegisterUserInput, RegisterUserUseCase
from src.shared.types.roles import Role
from src.shared.utils.time import utcnow
from tests.helpers import settings_kwargs
from tests.unit.fakes import FakePasswordHasher, InMemoryRefreshTokenRepository, InMemoryUserRepository

CLIENT = ClientInfo(ip="127.0.0.1", user_agent="pytest")
PASSWORD = "Catrina#2026"


@pytest.fixture
def token_service() -> JwtTokenService:
    settings = Settings(_env_file=None, **settings_kwargs())
    return JwtTokenService(settings)


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def refresh_tokens() -> InMemoryRefreshTokenRepository:
    return InMemoryRefreshTokenRepository()


@pytest.fixture
def login(users, refresh_tokens, token_service) -> LoginUseCase:
    return LoginUseCase(users, refresh_tokens, FakePasswordHasher(), token_service, LoginPolicy(3, 15))


async def _register(users: InMemoryUserRepository, email: str = "ana@example.com"):
    usecase = RegisterUserUseCase(users, FakePasswordHasher())
    return await usecase.execute(RegisterUserInput(name="Ana", email=email, phone="5512345678", password=PASSWORD))


async def test_register_normalizes_email_and_rejects_duplicates(users):
    user = await _register(users, "  Ana@Example.COM ")
    assert user.email == "ana@example.com"
    assert user.role is Role.USER
    assert user.password_hash != PASSWORD
    with pytest.raises(ConflictError):
        await _register(users, "ana@example.com")


async def test_login_issues_role_based_access_token(users, login, token_service):
    user = await _register(users)
    session = await login.execute(LoginInput(email="ana@example.com", password=PASSWORD, client=CLIENT))
    assert session.access_token.expires_in == 15 * 60
    assert token_service.verify_access_token(session.access_token.value).id == user.id


async def test_login_locks_account_after_max_attempts(users, login):
    user = await _register(users)
    for _ in range(3):
        with pytest.raises(UnauthorizedError):
            await login.execute(LoginInput(email=user.email, password="Mala#1234", client=CLIENT))
    assert users.users[user.id].locked_until is not None
    with pytest.raises(TooManyRequestsError):
        await login.execute(LoginInput(email=user.email, password=PASSWORD, client=CLIENT))


async def test_successful_login_resets_failed_attempts(users, login):
    user = await _register(users)
    with pytest.raises(UnauthorizedError):
        await login.execute(LoginInput(email=user.email, password="Mala#1234", client=CLIENT))
    await login.execute(LoginInput(email=user.email, password=PASSWORD, client=CLIENT))
    assert users.users[user.id].failed_login_attempts == 0


async def test_expired_lock_allows_login(users, login):
    user = await _register(users)
    users.users[user.id].locked_until = utcnow() - timedelta(seconds=1)
    session = await login.execute(LoginInput(email=user.email, password=PASSWORD, client=CLIENT))
    assert session.user.id == user.id


async def test_refresh_reuse_revokes_every_session(users, refresh_tokens, login, token_service):
    await _register(users)
    first = await login.execute(LoginInput(email="ana@example.com", password=PASSWORD, client=CLIENT))
    refresh = RefreshSessionUseCase(users, refresh_tokens, token_service)

    second = await refresh.execute(RefreshSessionInput(first.refresh_token.value, CLIENT))
    with pytest.raises(UnauthorizedError):
        await refresh.execute(RefreshSessionInput(first.refresh_token.value, CLIENT))
    with pytest.raises(UnauthorizedError):
        await refresh.execute(RefreshSessionInput(second.refresh_token.value, CLIENT))
