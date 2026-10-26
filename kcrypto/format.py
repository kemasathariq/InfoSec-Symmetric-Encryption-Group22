"""Format berkas terenkripsi (A1): SAMA untuk ketiga algoritma.

TODO: tentukan field header beserta panjang byte-nya dan tulis di docs/04-desain-kripto.md.
Bahan pertimbangan:
  - magic + versi (agar format bisa berkembang)
  - id algoritma
  - ukuran chunk dan ukuran plaintext asli
  - salt acak per berkas (untuk HKDF)
  - nonce / IV dasar (bila dipakai)
  - apa saja yang diikat ke tiap chunk: header, indeks, penanda chunk terakhir?
  - batas wajar nilai di header (cegah alokasi memori besar dari header palsu)
"""
