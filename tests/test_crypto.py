"""Tests for water heater payload decryption."""
import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import pytest

from vguard.crypto import VGuardCipher

KEY, IV = "0123456789abcdef", "fedcba9876543210"


def _encrypt(data: bytes) -> bytes:
    encryptor = Cipher(algorithms.AES(KEY.encode()), modes.CBC(IV.encode())).encryptor()
    return base64.b64encode(encryptor.update(data) + encryptor.finalize())


def test_decrypts_pkcs7():
    # '{"VG029":{}}' is 12 bytes, PKCS7 pads it with four 0x04 bytes
    payload = _encrypt(b'{"VG029":{}}' + b"\x04" * 4)
    assert VGuardCipher(KEY, IV).decrypt(payload) == '{"VG029":{}}'
    assert VGuardCipher(KEY, IV).decrypt(payload.decode()) == '{"VG029":{}}'


def test_decrypts_zero_padded():
    payload = _encrypt(b'{"VG029":{}}'.ljust(16, b"\x00"))
    assert VGuardCipher(KEY, IV).decrypt(payload) == '{"VG029":{}}'


@pytest.mark.parametrize("payload", ['{"VG029": {}}', "online", "", "QUJD"])
def test_decrypt_rejects_plain(payload):
    assert VGuardCipher(KEY, IV).decrypt(payload) is None


def test_key_length():
    with pytest.raises(ValueError):
        VGuardCipher("short", IV)
