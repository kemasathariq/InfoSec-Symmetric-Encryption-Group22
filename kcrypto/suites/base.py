"""Antarmuka internal sebuah suite (usulan; boleh diubah).

class Suite:
    name: str          # 'aes' | 'des' | 'rc4'
    algo_id: int       # nilai di header
    def derive(self, dek, header): ...                     # turunkan subkey per berkas
    def ct_len(self, pt_len) -> int: ...                   # ukuran chunk tersegel dari panjang plaintext
    def seal(self, keys, ctx, header, index, pt) -> bytes: ...
    def open(self, keys, ctx, header, index, blob) -> bytes: ...   # IntegrityError bila gagal

Dengan `ct_len`, panjang tiap chunk dapat dihitung dari header sehingga tidak perlu awalan panjang per chunk.
"""
