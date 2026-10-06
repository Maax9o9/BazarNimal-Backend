from abc import ABC, abstractmethod


class IFieldCipher(ABC):
    """Cifrado de datos personales a nivel de aplicación."""

    @abstractmethod
    def encrypt(self, plaintext: str, context: str) -> str:
        """`context` (por ejemplo, "users.email") liga el valor cifrado a su columna."""

    @abstractmethod
    def decrypt(self, ciphertext: str, context: str) -> str: ...

    @abstractmethod
    def blind_index(self, value: str) -> str:
        """Hash determinista (HMAC-SHA256) para búsquedas exactas sobre datos cifrados."""
