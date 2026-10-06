"""AES-256-GCM con versión de llave en el prefijo: "v1:<base64(nonce | ciphertext | tag)>"."""

import base64
import hashlib
import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.core.config.settings import Settings
from src.shared.contracts.field_cipher import IFieldCipher

NONCE_BYTES = 12


class DecryptionError(Exception):
    pass


class AesGcmFieldCipher(IFieldCipher):
    def __init__(self, settings: Settings) -> None:
        self._keys = {version: AESGCM(key) for version, key in settings.encryption_key_map.items()}
        self._active_version = settings.encryption_active_key_version
        self._hmac_key = settings.hmac_key.get_secret_value().encode()

    def encrypt(self, plaintext: str, context: str) -> str:
        nonce = os.urandom(NONCE_BYTES)
        ciphertext = self._keys[self._active_version].encrypt(nonce, plaintext.encode(), context.encode())
        return f"v{self._active_version}:{base64.urlsafe_b64encode(nonce + ciphertext).decode()}"

    def decrypt(self, ciphertext: str, context: str) -> str:
        prefix, _, encoded = ciphertext.partition(":")
        try:
            version = int(prefix.removeprefix("v"))
            raw = base64.urlsafe_b64decode(encoded)
            aesgcm = self._keys[version]
            return aesgcm.decrypt(raw[:NONCE_BYTES], raw[NONCE_BYTES:], context.encode()).decode()
        except (ValueError, KeyError, InvalidTag) as exc:
            raise DecryptionError("No se pudo descifrar el valor") from exc

    def blind_index(self, value: str) -> str:
        return hmac.new(self._hmac_key, value.encode(), hashlib.sha256).hexdigest()

    def needs_reencryption(self, ciphertext: str) -> bool:
        """True si el valor se cifró con una llave distinta a la activa (rotación de llaves)."""
        return not ciphertext.startswith(f"v{self._active_version}:")
