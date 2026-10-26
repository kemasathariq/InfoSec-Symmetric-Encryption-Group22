"""DES-CBC + HMAC-SHA256, encrypt-then-MAC (A3).

PERINGATAN (tulis juga di laporan): DES hanya 56-bit efektif dan berblok 64-bit; dipakai hanya karena diwajibkan tugas.
TODO: padding, IV per chunk, kunci MAC terpisah, urutan verifikasi (MAC dulu, baru dekripsi).
"""
