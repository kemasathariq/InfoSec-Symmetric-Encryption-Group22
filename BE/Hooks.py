"""
Titik colokan untuk enkripsi (BELUM diimplementasi).

Semua data privat (profil JSON + file KTP / dokumen kantor / video) lewat dua fungsi ini
sebelum ditulis ke disk/DB dan setelah dibaca kembali. Nanti cukup ubah isi fungsi ini
(dan CURRENT_CIPHER) untuk memasang AES / DES / RC4, route di app.py tidak perlu diubah.

`purpose` = "profile" | "ktp" | "supporting_doc" | "selfie_video"
`user_id` bisa dipakai untuk menurunkan key/IV/nonce per-user.
"""

CURRENT_CIPHER = "none"  # nanti: "aes" | "des" | "rc4"


def protect(data: bytes, *, user_id: int, purpose: str) -> bytes:
    return data  # TODO: encrypt


def unprotect(data: bytes, *, user_id: int, purpose: str) -> bytes:
    return data  # TODO: decrypt
