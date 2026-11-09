"""AES payload decryption for V-Guard water heaters.

V-Guard water heater messages may be AES-128-CBC encrypted and base64 encoded, using a
16-character key and IV per device. The V-Guard app gets them from V-Guard's cloud when the
device is added to an account.
"""
from __future__ import annotations

import base64
import binascii

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY_LENGTH = 16


class VGuardCipher:
    """Decrypt messages from one device."""

    def __init__(self, key: str, iv: str) -> None:
        self._key = key.encode()
        self._iv = iv.encode()
        if len(self._key) != KEY_LENGTH or len(self._iv) != KEY_LENGTH:
            raise ValueError("The key and IV must each be 16 characters")

    def _cipher(self) -> Cipher:
        return Cipher(algorithms.AES(self._key), modes.CBC(self._iv))

    def decrypt(self, payload: str | bytes) -> str | None:
        """Return the text of a base64 encrypted payload, or None if it isn't one."""
        try:
            data = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            return None
        if not data or len(data) % 16:
            return None
        decryptor = self._cipher().decryptor()
        plain = decryptor.update(data) + decryptor.finalize()
        # The app pads with PKCS7, the firmware may pad with zero bytes
        try:
            unpadder = padding.PKCS7(128).unpadder()
            plain = unpadder.update(plain) + unpadder.finalize()
        except ValueError:
            plain = plain.rstrip(b"\x00")
        try:
            return plain.decode()
        except UnicodeDecodeError:
            return None
