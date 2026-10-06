"""Los tokens viajan exclusivamente en cookies HttpOnly, Secure y SameSite."""

import secrets

from fastapi import Response

from src.core.config.settings import Settings

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
# El refresh token solo viaja a las rutas de auth que lo necesitan (refresh y logout).
REFRESH_COOKIE_PATH = "/api/v1/auth"


class CookieManager:
    def __init__(self, settings: Settings) -> None:
        self._secure = settings.cookie_secure
        self._samesite = settings.cookie_samesite
        self._domain = settings.cookie_domain
        self._csrf_enabled = settings.csrf_enabled

    def set_session(
        self,
        response: Response,
        *,
        access_token: str,
        access_expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
    ) -> None:
        self._set(response, ACCESS_COOKIE, access_token, access_expires_in, path="/")
        self._set(response, REFRESH_COOKIE, refresh_token, refresh_expires_in, path=REFRESH_COOKIE_PATH)
        if self._csrf_enabled:
            self._set(
                response,
                CSRF_COOKIE,
                secrets.token_urlsafe(32),
                refresh_expires_in,
                path="/",
                httponly=False,  # el frontend la lee para enviarla en el header X-CSRF-Token
            )

    def clear_session(self, response: Response) -> None:
        for name, path in (
            (ACCESS_COOKIE, "/"),
            (REFRESH_COOKIE, REFRESH_COOKIE_PATH),
            (CSRF_COOKIE, "/"),
        ):
            response.delete_cookie(
                name,
                path=path,
                domain=self._domain,
                secure=self._secure,
                httponly=name != CSRF_COOKIE,
                samesite=self._samesite,
            )

    def _set(
        self,
        response: Response,
        name: str,
        value: str,
        max_age: int,
        *,
        path: str,
        httponly: bool = True,
    ) -> None:
        response.set_cookie(
            name,
            value,
            max_age=max_age,
            path=path,
            domain=self._domain,
            secure=self._secure,
            httponly=httponly,
            samesite=self._samesite,
        )
