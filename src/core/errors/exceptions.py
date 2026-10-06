"""Errores de la aplicación. Son Python puro: los usan los casos de uso sin conocer HTTP."""


class AppError(Exception):
    status_code = 500
    default_message = "Error interno del servidor"

    def __init__(
        self,
        message: str | None = None,
        errors: list[dict[str, str]] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.errors = errors or []
        self.headers = headers or {}
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    default_message = "Solicitud inválida"


class UnauthorizedError(AppError):
    status_code = 401
    default_message = "No autorizado"


class ForbiddenError(AppError):
    status_code = 403
    default_message = "Acceso denegado"


class NotFoundError(AppError):
    status_code = 404
    default_message = "Recurso no encontrado"


class ConflictError(AppError):
    status_code = 409
    default_message = "El recurso está en un estado que no permite esta operación"


class InvalidDataError(AppError):
    status_code = 422
    default_message = "Datos inválidos"


class TooManyRequestsError(AppError):
    status_code = 429
    default_message = "Demasiadas peticiones, intenta más tarde"
