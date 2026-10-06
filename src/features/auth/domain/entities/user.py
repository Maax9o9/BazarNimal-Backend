from dataclasses import dataclass
from datetime import datetime

from src.shared.types.roles import Role


@dataclass(slots=True)
class User:
    id: str
    name: str
    email: str
    phone: str | None
    role: Role
    is_active: bool
    password_hash: str
    failed_login_attempts: int
    locked_until: datetime | None
    created_at: datetime

    def is_locked(self, now: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > now


@dataclass(frozen=True, slots=True)
class NewUser:
    name: str
    email: str
    phone: str
    password_hash: str
    role: Role = Role.USER
