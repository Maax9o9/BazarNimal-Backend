from sqlalchemy import RowMapping

from src.features.auth.data.dtos.auth_dtos import SessionDto, UserDto
from src.features.auth.domain.entities.session import AuthSession
from src.features.auth.domain.entities.user import User
from src.shared.contracts.field_cipher import IFieldCipher
from src.shared.types.roles import Role

EMAIL_CONTEXT = "users.email"
PHONE_CONTEXT = "users.phone"


class UserMapper:
    def __init__(self, cipher: IFieldCipher) -> None:
        self._cipher = cipher

    def to_entity(self, row: RowMapping) -> User:
        phone = row["phone_encrypted"]
        return User(
            id=row["id"],
            name=row["name"],
            email=self._cipher.decrypt(row["email_encrypted"], EMAIL_CONTEXT),
            phone=self._cipher.decrypt(phone, PHONE_CONTEXT) if phone else None,
            role=Role(row["role"]),
            is_active=bool(row["is_active"]),
            password_hash=row["password_hash"],
            failed_login_attempts=int(row["failed_login_attempts"]),
            locked_until=row["locked_until"],
            created_at=row["created_at"],
        )


def user_to_dto(user: User) -> UserDto:
    """Nunca expone password_hash ni datos de bloqueo."""
    return UserDto(id=user.id, name=user.name, email=user.email, phone=user.phone, role=user.role)


def session_to_dto(session: AuthSession) -> SessionDto:
    return SessionDto(
        user=user_to_dto(session.user),
        role=session.user.role,
        expires_in=session.access_token.expires_in,
    )
