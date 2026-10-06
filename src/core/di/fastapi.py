"""Puente entre el contenedor y FastAPI: un scope por petición y `inject(Clase)` en las rutas."""

from collections.abc import AsyncIterator
from typing import Any

from fastapi import Depends, Request

from src.core.di.container import Container, Scope


def get_container(request: Request) -> Container:
    return request.app.state.container


async def get_scope(request: Request) -> AsyncIterator[Scope]:
    scope = get_container(request).create_scope()
    try:
        yield scope
    finally:
        await scope.aclose()


def inject(key: Any) -> Any:
    """Uso: `controller: PetAdminController = inject(PetAdminController)`."""

    def _resolve(scope: Scope = Depends(get_scope)) -> Any:
        return scope.resolve(key)

    return Depends(_resolve)
