from dataclasses import dataclass

from src.shared.types.roles import Role


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """Identidad autenticada tomada del JWT (solo `sub` y `role`)."""

    id: str
    role: Role
