"""Esquemas y tipos de validación reutilizables."""

import re
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints

from src.shared.types.pagination import PageRequest

MAX_PAGE_LIMIT = 100


class StrictSchema(BaseModel):
    """Lista blanca de campos: cualquier propiedad no declarada se rechaza (evita mass assignment)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _empty_to_none(value: Any) -> Any:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


# Los formularios multipart envían "" cuando un campo opcional va vacío.
EmptyAsNone = BeforeValidator(_empty_to_none)


class PaginationQuery(StrictSchema):
    page: int = Field(default=1, ge=1, le=100_000)
    limit: int = Field(default=20, ge=1, le=MAX_PAGE_LIMIT)

    def to_page_request(self) -> PageRequest:
        return PageRequest(page=self.page, limit=self.limit)


_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '.\-][^\W\d_]+)*\.?$", re.UNICODE)
_PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


def _person_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip())
    if not _NAME_RE.match(value):
        raise ValueError("Solo se permiten letras, espacios, apóstrofos, puntos y guiones")
    return value


def _phone(value: str) -> str:
    value = re.sub(r"[\s\-()]", "", value)
    if not _PHONE_RE.match(value):
        raise ValueError("El teléfono debe tener entre 10 y 15 dígitos (puede iniciar con +)")
    return value


def check_password_policy(value: str) -> str:
    checks = [
        (len(value) >= 8, "al menos 8 caracteres"),
        (re.search(r"[A-Z]", value), "una mayúscula"),
        (re.search(r"[a-z]", value), "una minúscula"),
        (re.search(r"[0-9]", value), "un número"),
        (re.search(r"[^A-Za-z0-9]", value), "un símbolo"),
    ]
    missing = [text for passed, text in checks if not passed]
    if missing:
        raise ValueError("La contraseña debe tener " + ", ".join(missing))
    return value


PersonName = Annotated[str, StringConstraints(min_length=2, max_length=100), AfterValidator(_person_name)]
PhoneNumber = Annotated[str, StringConstraints(max_length=20), AfterValidator(_phone)]
StrongPassword = Annotated[str, StringConstraints(max_length=128), AfterValidator(check_password_policy)]
