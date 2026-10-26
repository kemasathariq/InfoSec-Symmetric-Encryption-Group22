"""Manajemen kunci (A5).

Hierarki yang diusulkan (finalkan di docs/04):
    password --Argon2id(salt)--> KEK        (hanya di memori selama sesi)
    KEK  membungkus  kunci pengguna (UK)    (disimpan terbungkus di DB)
    UK   membungkus  DEK per item           (disimpan terbungkus di DB)
    DEK --HKDF--> subkey tiap algoritma
"""
from __future__ import annotations


def new_key(n: int = 32) -> bytes:
    """Kunci acak dari CSPRNG sistem operasi."""
    raise NotImplementedError("TODO A5")


def new_salt(n: int = 16) -> bytes:
    raise NotImplementedError("TODO A5")


def derive_kek(password: str, salt: bytes) -> bytes:
    """Argon2id -> kunci 32 byte. Putuskan parameter (waktu, memori, paralelisme) dan dokumentasikan alasannya."""
    raise NotImplementedError("TODO A5")


def hkdf(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    """HKDF-SHA256. `info` membedakan tujuan kunci (domain separation)."""
    raise NotImplementedError("TODO A5")


def wrap_key(wrapping_key: bytes, key: bytes, aad: bytes = b"") -> bytes:
    """Bungkus `key` dengan AEAD. `aad` (mis. id item) mengikat hasil ke konteksnya."""
    raise NotImplementedError("TODO A5")


def unwrap_key(wrapping_key: bytes, blob: bytes, aad: bytes = b"") -> bytes:
    """Kebalikan wrap_key. Lempar IntegrityError bila kunci / aad salah atau blob diubah."""
    raise NotImplementedError("TODO A5")
