import os

import pytest

from kcrypto import TEST_KDF, IntegrityError, derive_kek, new_key, new_salt, unwrap_key, wrap_key


def test_kdf_deterministic_and_salted():
    s = new_salt()
    assert derive_kek("pw", s, TEST_KDF) == derive_kek("pw", s, TEST_KDF)
    assert derive_kek("pw", s, TEST_KDF) != derive_kek("pw", new_salt(), TEST_KDF)
    assert derive_kek("pw", s, TEST_KDF) != derive_kek("pw2", s, TEST_KDF)
    assert len(derive_kek("pw", s, TEST_KDF)) == 32


def test_kdf_unicode_normalisation():
    s = new_salt()
    assert derive_kek("\u00e9", s, TEST_KDF) == derive_kek("e\u0301", s, TEST_KDF)


def test_wrap_roundtrip_and_aad_binding():
    kek, dek = new_key(), new_key()
    blob = wrap_key(kek, dek, aad=b"item-1")
    assert unwrap_key(kek, blob, aad=b"item-1") == dek
    with pytest.raises(IntegrityError):
        unwrap_key(kek, blob, aad=b"item-2")  # wrapped key can't be moved to another item
    with pytest.raises(IntegrityError):
        unwrap_key(new_key(), blob, aad=b"item-1")  # wrong KEK (e.g. wrong password)


def test_wrap_tamper():
    kek = new_key()
    blob = bytearray(wrap_key(kek, new_key()))
    for i in range(len(blob)):
        bad = bytearray(blob)
        bad[i] ^= 1
        with pytest.raises(IntegrityError):
            unwrap_key(kek, bytes(bad))


def test_full_hierarchy():
    salt = new_salt()
    kek = derive_kek("correct horse", salt, TEST_KDF)
    uk, dek = new_key(), new_key()
    wuk, wdek = wrap_key(kek, uk), wrap_key(uk, dek, aad=b"item")
    uk2 = unwrap_key(derive_kek("correct horse", salt, TEST_KDF), wuk)
    assert unwrap_key(uk2, wdek, aad=b"item") == dek
    with pytest.raises(IntegrityError):
        unwrap_key(derive_kek("wrong", salt, TEST_KDF), wuk)
