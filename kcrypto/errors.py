"""Jenis error modul kripto (bagian dari kontrak)."""


class CryptoError(Exception):
    """Induk semua error kcrypto."""


class IntegrityError(CryptoError):
    """Data gagal autentikasi / struktur tidak valid / kunci salah.

    Pesan sengaja tidak memberi tahu bagian mana yang gagal.
    """


class UnsupportedAlgorithm(CryptoError, ValueError):
    """Nama / id algoritma tidak dikenal."""
