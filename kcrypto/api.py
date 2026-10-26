"""KONTRAK ANTARMUKA modul kripto: dipakai oleh backend (B) dan benchmark (D).

Mengubah tanda tangan di sini harus lewat PR yang disetujui A dan B.

Catatan untuk pemanggil:
  * Tiap chunk diautentikasi sendiri. Bila IntegrityError dilempar, sebagian chunk awal mungkin sudah
    tertulis ke `dst`: pemanggil WAJIB membuang output tersebut.
  * `src` pada enkripsi harus seekable (atau berikan orig_size).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Callable, Dict, Optional

from .errors import IntegrityError  # noqa: F401  (diekspor sebagai bagian kontrak)

ALGOS = ("aes", "des", "rc4")
DEFAULT_CHUNK = 1 << 20  # 1 MiB (usulan; finalkan di docs/04)


@dataclass(frozen=True)
class CryptoMeta:
    algo: str
    header_len: int
    pt_size: int
    ct_size: int                    # total byte hasil, termasuk header
    pt_sha256: Optional[bytes]
    ct_sha256: Optional[bytes]
    seconds: float


@dataclass(frozen=True)
class VerifyReport:
    ok: bool                                  # semua salinan lolos DAN hash plaintext semuanya sama
    pt_sha256: Dict[str, Optional[bytes]]     # per algoritma; None bila salinan itu gagal
    failed: tuple                             # algoritma yang salinannya gagal


def encrypt_stream(
    src: BinaryIO, dst: BinaryIO, dek: bytes, algo: str,
    *, chunk_size: int = DEFAULT_CHUNK, orig_size: Optional[int] = None,
) -> CryptoMeta:
    """Enkripsi aliran `src` ke `dst` dengan `algo` ('aes'|'des'|'rc4') memakai kunci per-item `dek` (32 byte)."""
    raise NotImplementedError("TODO A2-A4, A6")


def decrypt_stream(
    src: BinaryIO, dst: BinaryIO, dek: bytes, algo: Optional[str] = None,
) -> CryptoMeta:
    """Dekripsi + verifikasi. Lempar IntegrityError bila gagal. Bila `algo` diberikan, harus cocok dengan header."""
    raise NotImplementedError("TODO A2-A4, A6")


def encrypt_all(
    src: BinaryIO, open_dst: Callable[[str], BinaryIO], dek: bytes, algos=ALGOS,
) -> Dict[str, CryptoMeta]:
    """Satu sumber menjadi satu salinan per algoritma. `open_dst(algo)` mengembalikan berkas tujuan untuk salinan itu."""
    raise NotImplementedError("TODO A6")


def verify_copies(open_src: Callable[[str], BinaryIO], dek: bytes, algos=ALGOS) -> VerifyReport:
    """Dekripsi semua salinan (output dibuang) dan bandingkan hash plaintext-nya."""
    raise NotImplementedError("TODO A6")
