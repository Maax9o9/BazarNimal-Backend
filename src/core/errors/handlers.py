"""Manejador global de errores.

Al cliente nunca se le envían stack traces, mensajes de SQL ni rutas internas.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.errors.exceptions import AppError
from src.core.logger.logger import get_logger, security_logger

logger = get_logger("errors")

_HTTP_MESSAGES = {
    400: "Solicitud inválida",
    401: "No autorizado",
    403: "Acceso denegado",
    404: "Recurso no encontrado",
    405: "Método no permitido",
    409: "Conflicto",
    413: "El cuerpo de la petición es demasiado grande",
    415: "Tipo de contenido no soportado",
    422: "Datos inválidos",
    429: "Demasiadas peticiones, intenta más tarde",
}

_LOCATION_PREFIXES = {"body", "query", "path", "header", "cookie"}


def error_body(message: str, errors: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {"success": False, "message": message, "errors": errors or []}


def _translate(error: dict[str, Any]) -> str:
    kind = error.get("type", "")
    ctx = error.get("ctx") or {}
    if kind == "value_error" and "email address" in str(error.get("msg", "")):
        return "El formato del correo no es válido"
    match kind:
        case "missing":
            return "Este campo es obligatorio"
        case "extra_forbidden":
            return "Campo no permitido"
        case "string_too_short":
            return f"Debe tener al menos {ctx.get('min_length')} caracteres"
        case "string_too_long":
            return f"Debe tener como máximo {ctx.get('max_length')} caracteres"
        case "string_pattern_mismatch":
            return "El formato no es válido"
        case "string_type":
            return "Debe ser texto"
        case "int_parsing" | "int_type" | "int_from_float":
            return "Debe ser un número entero"
        case "float_parsing" | "float_type" | "decimal_parsing" | "decimal_type":
            return "Debe ser un número"
        case "decimal_max_places":
            return f"Debe tener como máximo {ctx.get('decimal_places')} decimales"
        case "greater_than_equal":
            return f"Debe ser mayor o igual a {ctx.get('ge')}"
        case "greater_than":
            return f"Debe ser mayor a {ctx.get('gt')}"
        case "less_than_equal":
            return f"Debe ser menor o igual a {ctx.get('le')}"
        case "less_than":
            return f"Debe ser menor a {ctx.get('lt')}"
        case "enum" | "literal_error":
            return f"Valor no permitido. Opciones: {ctx.get('expected')}"
        case "uuid_parsing" | "uuid_type":
            return "Identificador inválido"
        case "bool_parsing" | "bool_type":
            return "Debe ser verdadero o falso"
        case "json_invalid":
            return "El JSON no es válido"
        case "model_attributes_type" | "dict_type" | "model_type":
            return "El formato del cuerpo no es válido"
        case "value_error" | "assertion_error":
            message = str(error.get("msg", "Valor inválido"))
            return message.removeprefix("Value error, ").removeprefix("Assertion failed, ")
        case "value_error.email" | "email":
            return "El formato del correo no es válido"
    if "email" in str(error.get("msg", "")).lower():
        return "El formato del correo no es válido"
    return "Valor inválido"


def _field_name(location: tuple[Any, ...] | list[Any]) -> str:
    parts = [str(part) for part in location]
    if parts and parts[0] in _LOCATION_PREFIXES:
        parts = parts[1:]
    return ".".join(parts) or "request"


async def app_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    if exc.status_code == 403:
        security_logger.warning(
            "access_denied",
            extra={"path": request.url.path, "ip": request.client.host if request.client else None},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(exc.message, exc.errors),
        headers=exc.headers or None,
    )


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = [
        {"field": _field_name(error.get("loc", ())), "message": _translate(error)}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content=error_body("Datos inválidos", errors))


async def http_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    message = _HTTP_MESSAGES.get(exc.status_code, "Error en la petición")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_body(message),
        headers=getattr(exc, "headers", None),
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error", extra={"path": request.url.path, "method": request.method})
    return JSONResponse(status_code=500, content=error_body("Error interno del servidor"))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
