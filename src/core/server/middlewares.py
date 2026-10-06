
import hmac
import json
import time

from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.core.logger.logger import get_logger, security_logger
from src.core.security.cookies import CSRF_COOKIE, CSRF_HEADER
from src.core.security.rate_limit import IRateLimitStore, rate_limit_headers

request_logger = get_logger("http")

_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")
_UPLOADS_PATH = "/uploads/"

_API_CSP = "default-src 'none'; frame-ancestors 'none'"
_DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
    "worker-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'"
)
_UPLOADS_CSP = "default-src 'none'; img-src 'self'; sandbox"


async def _send_json(send: Send, status: int, body: dict, headers: dict[str, str] | None = None) -> None:
    payload = json.dumps(body, ensure_ascii=False).encode()
    raw_headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(payload)).encode()),
    ]
    raw_headers += [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    await send({"type": "http.response.start", "status": status, "headers": raw_headers})
    await send({"type": "http.response.body", "body": payload})


def _client_ip(scope: Scope) -> str:
    client = scope.get("client")
    return client[0] if client else "unknown"


class SecurityHeadersMiddleware:
    """Equivalente a Helmet: CSP, HSTS, nosniff, frame-options, referrer-policy."""

    def __init__(self, app: ASGIApp, *, hsts: bool) -> None:
        self.app = app
        self.hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path: str = scope["path"]
        is_docs = path.startswith(_DOCS_PATHS)
        is_upload = path.startswith(_UPLOADS_PATH)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Cross-Origin-Opener-Policy"] = "same-origin"
                headers["Cross-Origin-Resource-Policy"] = "cross-origin" if is_upload else "same-origin"
                headers["Content-Security-Policy"] = (
                    _DOCS_CSP if is_docs else _UPLOADS_CSP if is_upload else _API_CSP
                )
                if not is_docs and not is_upload:
                    headers["Cache-Control"] = "no-store"
                if self.hsts:
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                for name in ("x-powered-by", "server"):
                    if name in headers:
                        del headers[name]
            await send(message)

        await self.app(scope, receive, send_wrapper)


class BodySizeLimitMiddleware:
    """Límite de tamaño del body: JSON pequeño, multipart hasta el tamaño máximo de imagen."""

    def __init__(self, app: ASGIApp, *, json_limit: int, multipart_limit: int) -> None:
        self.app = app
        self.json_limit = json_limit
        self.multipart_limit = multipart_limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        is_multipart = headers.get("content-type", "").startswith("multipart/form-data")
        limit = self.multipart_limit if is_multipart else self.json_limit
        declared = headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > limit:
            await _send_json(send, 413, _error("El cuerpo de la petición es demasiado grande"))
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    # FastAPI propaga HTTPException al leer el body; el manejador global responde 413.
                    raise HTTPException(status_code=413)
            return message

        await self.app(scope, limited_receive, send)


class RequestLoggingMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_logger.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_holder["status"],
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                    "ip": _client_ip(scope),
                },
            )


class GlobalRateLimitMiddleware:
    """Límite global por IP. Si una ruta tiene su propio límite, sus headers tienen prioridad."""

    def __init__(self, app: ASGIApp, *, store: IRateLimitStore, limit: int, window_seconds: int) -> None:
        self.app = app
        self.store = store
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        if (
            scope["type"] != "http"
            or scope["method"] == "OPTIONS"
            or path.startswith(_DOCS_PATHS)
            or path.startswith(_UPLOADS_PATH)
            or path == "/health"
        ):
            await self.app(scope, receive, send)
            return

        ip = _client_ip(scope)
        result = await self.store.hit(f"global:{ip}", self.limit, self.window_seconds)
        headers = rate_limit_headers(result)
        if not result.allowed:
            security_logger.warning("rate_limit_exceeded", extra={"policy": "global", "ip": ip, "path": path})
            await _send_json(send, 429, _error("Demasiadas peticiones, intenta más tarde"), headers)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                if "ratelimit-limit" not in response_headers:
                    for name, value in headers.items():
                        response_headers[name] = value
            await send(message)

        await self.app(scope, receive, send_wrapper)


class CsrfMiddleware:
    """Doble token (cookie + header X-CSRF-Token). Obligatorio cuando SameSite=None."""

    _SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    def __init__(self, app: ASGIApp, *, exempt_paths: set[str]) -> None:
        self.app = app
        self.exempt_paths = exempt_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] in self._SAFE_METHODS
            or scope["path"] in self.exempt_paths
        ):
            await self.app(scope, receive, send)
            return
        headers = Headers(scope=scope)
        cookie_token = _read_cookie(headers.get("cookie", ""), CSRF_COOKIE)
        header_token = headers.get(CSRF_HEADER, "")
        if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
            security_logger.warning("csrf_rejected", extra={"ip": _client_ip(scope), "path": scope["path"]})
            await _send_json(send, 403, _error("Token CSRF inválido"))
            return
        await self.app(scope, receive, send)


def _read_cookie(cookie_header: str, name: str) -> str | None:
    for part in cookie_header.split(";"):
        key, _, value = part.strip().partition("=")
        if key == name:
            return value
    return None


def _error(message: str) -> dict:
    return {"success": False, "message": message, "errors": []}
