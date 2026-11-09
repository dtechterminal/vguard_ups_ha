"""Tests for water heater payload encryption."""
import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import pytest

from vguard.crypto import VGuardCipher

KEY, IV = "0123456789abcdef", "fedcba9876543210"


def test_round_trip():
    cipher = VGuardCipher(KEY, IV)
    payload = cipher.encrypt("VG094:1")
    assert payload != "VG094:1"
    assert cipher.decrypt(payload) == "VG094:1"


def test_matches_aes_cbc_pkcs7():
    # "VG094:1" is 7 bytes, PKCS7 pads it with nine 0x09 bytes
    encryptor = Cipher(algorithms.AES(KEY.encode()), modes.CBC(IV.encode())).encryptor()
    expected = encryptor.update(b"VG094:1" + b"\x09" * 9) + encryptor.finalize()
    assert VGuardCipher(KEY, IV).encrypt("VG094:1") == base64.b64encode(expected).decode()


def test_decrypts_zero_padded():
    encryptor = Cipher(algorithms.AES(KEY.encode()), modes.CBC(IV.encode())).encryptor()
    data = encryptor.update(b'{"VG029":{}}'.ljust(16, b"\x00")) + encryptor.finalize()
    assert VGuardCipher(KEY, IV).decrypt(base64.b64encode(data)) == '{"VG029":{}}'


@pytest.mark.parametrize("payload", ['{"VG029": {}}', "online", "", "QUJD"])
def test_decrypt_rejects_plain(payload):
    assert VGuardCipher(KEY, IV).decrypt(payload) is None


def test_key_length():
    with pytest.raises(ValueError):
        VGuardCipher("short", IV)
