
import hashlib
import json
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.core.config.settings import Settings
from src.core.di.fastapi import inject
from src.core.errors.exceptions import TooManyRequestsError
from src.core.logger.logger import security_logger
from src.core.security.rate_limit import IRateLimitStore, RateLimitResult, rate_limit_headers

KeyFunc = Callable[[Request], Awaitable[str | None]]


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def by_ip(request: Request) -> str | None:
    return f"ip:{client_ip(request)}"


async def by_user(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    return f"user:{user.id}" if user else None


async def by_body_email(request: Request) -> str | None:
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    email = body.get("email") if isinstance(body, dict) else None
    if not isinstance(email, str) or not email.strip():
        return None
    return "email:" + hashlib.sha256(email.strip().lower().encode()).hexdigest()


def rate_limit(policy: str, *keys: KeyFunc) -> Callable[..., Awaitable[None]]:
    key_funcs = keys or (by_ip,)

    async def dependency(
        request: Request,
        response: Response,
        settings: Settings = inject(Settings),
        store: IRateLimitStore = inject(IRateLimitStore),
    ) -> None:
        limit, window = settings.rate_limit_policy(policy)
        tightest: RateLimitResult | None = None
        for key_func in key_funcs:
            key = await key_func(request)
            if key is None:
                continue
            result = await store.hit(f"{policy}:{key}", limit, window)
            if not result.allowed:
                security_logger.warning(
                    "rate_limit_exceeded",
                    extra={"policy": policy, "ip": client_ip(request), "path": request.url.path},
                )
                raise TooManyRequestsError(headers=rate_limit_headers(result))
            if tightest is None or result.remaining < tightest.remaining:
                tightest = result
        if tightest is not None:
            response.headers.update(rate_limit_headers(tightest))

    return dependency

