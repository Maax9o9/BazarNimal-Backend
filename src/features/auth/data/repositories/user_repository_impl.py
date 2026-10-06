from datetime import datetime

from sqlalchemy import exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors.exceptions import ConflictError
from src.features.auth.data.mappers.user_mapper import EMAIL_CONTEXT, PHONE_CONTEXT, UserMapper
from src.features.auth.data.models.auth_tables import users
from src.features.auth.domain.entities.user import NewUser, User
from src.features.auth.domain.repositories.user_repository import IUserRepository
from src.shared.contracts.field_cipher import IFieldCipher
from src.shared.utils.ids import new_id
from src.shared.utils.time import utcnow


class UserRepositoryImpl(IUserRepository):
    def __init__(self, session: AsyncSession, cipher: IFieldCipher, mapper: UserMapper) -> None:
        self._session = session
        self._cipher = cipher
        self._mapper = mapper

    async def find_by_email(self, email: str) -> User | None:
        query = select(users).where(
            users.c.email_hash == self._cipher.blind_index(email),
            users.c.deleted_at.is_(None),
        )
        row = (await self._session.execute(query)).mappings().first()
        return self._mapper.to_entity(row) if row else None

    async def find_by_id(self, user_id: str) -> User | None:
        query = select(users).where(users.c.id == user_id, users.c.deleted_at.is_(None))
        row = (await self._session.execute(query)).mappings().first()
        return self._mapper.to_entity(row) if row else None

    async def exists_by_email(self, email: str) -> bool:
        # Incluye usuarios borrados lógicamente: email_hash es UNIQUE en la tabla.
        query = select(exists().where(users.c.email_hash == self._cipher.blind_index(email)))
        return bool(await self._session.scalar(query))

    async def create(self, data: NewUser) -> User:
        now = utcnow()
        user = User(
            id=new_id(),
            name=data.name,
            email=data.email,
            phone=data.phone,
            role=data.role,
            is_active=True,
            password_hash=data.password_hash,
            failed_login_attempts=0,
            locked_until=None,
            created_at=now,
        )
        try:
            await self._session.execute(
                users.insert().values(
                    id=user.id,
                    name=user.name,
                    email_encrypted=self._cipher.encrypt(user.email, EMAIL_CONTEXT),
                    email_hash=self._cipher.blind_index(user.email),
                    password_hash=user.password_hash,
                    phone_encrypted=self._cipher.encrypt(data.phone, PHONE_CONTEXT),
                    role=user.role.value,
                    is_active=True,
                    failed_login_attempts=0,
                    created_at=now,
                    updated_at=now,
                )
            )
            await self._session.commit()
        except IntegrityError:
            # Dos registros simultáneos con el mismo correo: gana el primero.
            await self._session.rollback()
            raise ConflictError("El correo ya está registrado") from None
        return user

    async def record_failed_login(self, user_id: str, attempts: int, locked_until: datetime | None) -> None:
        await self._update(user_id, failed_login_attempts=attempts, locked_until=locked_until)

    async def reset_failed_logins(self, user_id: str) -> None:
        await self._update(user_id, failed_login_attempts=0, locked_until=None)

    async def update_password_hash(self, user_id: str, password_hash: str) -> None:
        await self._update(user_id, password_hash=password_hash)

    async def _update(self, user_id: str, **values: object) -> None:
        await self._session.execute(
            update(users).where(users.c.id == user_id).values(**values, updated_at=utcnow())
        )
        await self._session.commit()
