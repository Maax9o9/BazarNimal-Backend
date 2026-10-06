import anyio
from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from src.shared.contracts.password_hasher import IPasswordHasher


class Argon2PasswordHasher(IPasswordHasher):
    """Argon2id. El cálculo corre en un hilo para no bloquear el event loop."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=2, type=Type.ID)

    async def hash(self, password: str) -> str:
        return await anyio.to_thread.run_sync(self._hasher.hash, password)

    async def verify(self, password_hash: str, password: str) -> bool:
        def _verify() -> bool:
            try:
                return self._hasher.verify(password_hash, password)
            except (VerifyMismatchError, VerificationError, InvalidHashError):
                return False

        return await anyio.to_thread.run_sync(_verify)

    def needs_rehash(self, password_hash: str) -> bool:
        return self._hasher.check_needs_rehash(password_hash)
