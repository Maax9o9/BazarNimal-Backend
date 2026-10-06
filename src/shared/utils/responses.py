"""Formato estándar de respuestas: { success, data, message } / { success, data, meta }."""

from typing import Literal

from pydantic import BaseModel

from src.shared.types.pagination import Page


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    message: str
    errors: list[FieldError] = []


class SuccessResponse[T](BaseModel):
    success: Literal[True] = True
    data: T
    message: str | None = None


class MessageResponse(BaseModel):
    success: Literal[True] = True
    message: str


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int


class PaginatedResponse[T](BaseModel):
    success: Literal[True] = True
    data: list[T]
    meta: PageMeta


def ok[T](data: T, message: str | None = None) -> SuccessResponse[T]:
    return SuccessResponse[T](data=data, message=message)


def paginated[T](items: list[T], page: Page) -> PaginatedResponse[T]:
    return PaginatedResponse[T](
        data=items,
        meta=PageMeta(page=page.page, limit=page.limit, total=page.total),
    )


# Respuestas de error documentadas en Swagger.
ERROR_RESPONSES: dict[int | str, dict] = {
    401: {"model": ErrorResponse, "description": "No autenticado"},
    403: {"model": ErrorResponse, "description": "Sin permisos"},
    404: {"model": ErrorResponse, "description": "No encontrado"},
    409: {"model": ErrorResponse, "description": "Conflicto con el estado actual"},
    422: {"model": ErrorResponse, "description": "Datos inválidos"},
    429: {"model": ErrorResponse, "description": "Demasiadas peticiones"},
}


def errors(*codes: int) -> dict[int | str, dict]:
    return {code: ERROR_RESPONSES[code] for code in codes}
