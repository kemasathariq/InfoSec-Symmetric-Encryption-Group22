# kcrypto: modul kripto (Anggota A)

**Tugas:** A1-A10 di `TASKS.md`. **Status: hanya kerangka.**
Tujuan: B bisa mengenkripsi dan mendekripsi tanpa tahu detail tiap algoritma.

## Yang harus dihasilkan
- [ ] `docs/04-desain-kripto.md` terisi (A1), dikunci di hari 0
- [ ] Tiga implementasi di `suites/` (A2-A4)
- [ ] `keys.py` (A5)
- [ ] `api.py` sesuai kontrak (A6)
- [ ] Tes lolos (A7), uji file besar (A8)

## Kontrak (jangan diubah tanpa persetujuan B)
Lihat `api.py`. Ringkasnya:
- `encrypt_stream(src, dst, dek, algo)` / `decrypt_stream(src, dst, dek, algo)`: aliran, tidak memuat seluruh file ke RAM
- `encrypt_all(...)`: satu sumber menjadi 3 salinan
- `verify_copies(...)`: dekripsi 3 salinan dan bandingkan hash plaintext
- `IntegrityError`: dilempar bila data berubah / rusak / kunci salah (tanpa memberi tahu bagian mana yang gagal)

## Rekomendasi desain (boleh diubah asal alasannya dicatat di docs/04)

| Cipher | Usulan | Hal yang harus kamu putuskan |
|---|---|---|
| AES | AES-256-**GCM** (integritas bawaan) | Cara membentuk nonce 12 byte agar tidak pernah berulang; data apa yang masuk AAD |
| DES | **CBC** + padding PKCS7 + **HMAC-SHA256** (encrypt-then-MAC) | Blok 64-bit: berapa batas data per kunci? IV acak per chunk; kunci MAC terpisah |
| RC4 | stream cipher + **HMAC-SHA256** | RC4 tidak punya IV: bagaimana menjamin kunci tidak dipakai ulang? (usulan: kunci baru per chunk dari HKDF.) Perlukah membuang awal keystream? |

Prinsip umum:
- **Jangan ECB.** Jelaskan alasannya di docs/04.
- Satu DEK per item; subkey tiap algoritma diturunkan dengan HKDF dan label berbeda (ketiganya independen).
- Hierarki kunci: `password -> Argon2id -> KEK -> kunci pengguna -> DEK per item`. Wrap kunci dengan AEAD dan ikat ke id item (AAD).
- Header ikut diautentikasi; indeks chunk dan penanda chunk terakhir terikat ke tiap chunk (mencegah reorder dan truncation).
- Batasi `chunk_size` dari header (mencegah header palsu memaksa alokasi besar).
- Bandingkan tag/MAC dengan fungsi waktu-konstan; verifikasi MAC **sebelum** dekripsi (DES/RC4).

## Tes yang harus ditulis (`tests/`)
Daftar ada di berkas tes (saat ini ditandai skip). Minimal:
1. Round-trip untuk ukuran: 0, 1, batas blok, batas chunk, banyak chunk
2. Plaintext sama dienkripsi dua kali menghasilkan ciphertext berbeda
3. Mengubah **setiap** byte (header, IV, ciphertext, tag/MAC) memicu `IntegrityError`
4. Pemotongan, penambahan, penukaran urutan chunk, penyambungan chunk antar file
5. Kunci salah dan algoritma salah
6. Test vector resmi untuk primitif (NIST GCM, DES, RC4, RFC 5869 untuk HKDF)
7. Tes statis: tidak ada `MODE_ECB` di kode produk

## Catatan
- Library: PyCryptodome (menyediakan AES, DES, ARC4 langsung).
- Mulai dari `format.py` dan satu cipher (AES) end-to-end, baru tambah dua lainnya.
- Selesaikan A6 lebih awal supaya D bisa mulai benchmark dan B bisa mengganti mock.
