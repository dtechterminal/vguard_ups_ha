"""AES payload encryption used by V-Guard water heaters.

The V-Guard app encrypts device commands with AES-128-CBC, PKCS7 padding and base64, using
a 16-character key and IV per device. The app gets them from V-Guard's cloud when the device
is added to an account.
"""
from __future__ import annotations

import base64
import binascii

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY_LENGTH = 16


class VGuardCipher:
    """Encrypt commands for, and decrypt messages from, one device."""

    def __init__(self, key: str, iv: str) -> None:
        self._key = key.encode()
        self._iv = iv.encode()
        if len(self._key) != KEY_LENGTH or len(self._iv) != KEY_LENGTH:
            raise ValueError("The key and IV must each be 16 characters")

    def _cipher(self) -> Cipher:
        return Cipher(algorithms.AES(self._key), modes.CBC(self._iv))

    def encrypt(self, text: str) -> str:
        """Return `text` encrypted and base64 encoded."""
        padder = padding.PKCS7(128).padder()
        data = padder.update(text.encode()) + padder.finalize()
        encryptor = self._cipher().encryptor()
        return base64.b64encode(encryptor.update(data) + encryptor.finalize()).decode()

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
