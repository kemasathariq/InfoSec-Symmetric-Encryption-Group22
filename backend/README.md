# backend: API, auth, DB, audit (Anggota B)

**Tugas:** B0-B10 di `TASKS.md`. **Status: hanya kerangka.**

## Yang harus dihasilkan
- [ ] Mock modul kripto agar tidak menunggu A (B0)
- [ ] Skema DB + migrasi (B1)
- [ ] Registrasi / login / sesi / rate limit (B2)
- [ ] Otorisasi pemilik-saja (B3)
- [ ] Endpoint profil, upload, download, verifikasi, hapus, audit (B4-B7)
- [ ] TLS (B8), tes keamanan (B9)
- [ ] `openapi.yaml` lengkap dengan skema request/response

## Tabel DB yang perlu dirancang (nama kolom adalah usulan)

| Tabel | Kolom penting | Catatan |
|---|---|---|
| `users` | id, email (unik), hash password, salt KDF, kunci pengguna terbungkus, percobaan gagal, terkunci sampai | Salt untuk hash login dan salt untuk KEK **berbeda** |
| `items` | id, owner_id, kind (profile/id_scan/document/video), metadata terenkripsi, DEK terbungkus, HMAC plaintext, waktu | Nama berkas asli bisa membocorkan isi, jadi enkripsi. Hash plaintext polos bisa membocorkan kesamaan berkas: pikirkan HMAC berkunci server |
| `item_copies` | id, item_id, algo, path storage, panjang header, ukuran, hash ciphertext | unik (item_id, algo): tepat 3 baris per item |
| `audit_log` | id, waktu, user_id, aksi, item_id, algo, ip, hasil, hash sebelumnya, hash baris | rantai hash agar perubahan terdeteksi |

## Aturan keamanan yang harus dipenuhi
1. Pengecekan kepemilikan **di server** pada setiap akses item. Item milik orang lain dijawab **404**, bukan 403.
2. Kunci pengguna hanya hidup di memori server selama sesi (dengan batas waktu). Tidak pernah ditulis ke disk atau log.
3. Password di-hash dengan Argon2id; pesan error login sama untuk "email salah" dan "password salah".
4. Rate limit dan lockout pada login.
5. Jangan pernah log: password, kunci, isi data.
6. Saat dekripsi gagal (`IntegrityError`), jangan kirim output parsial sebagai file valid; catat di audit log.
7. Bergantung pada HTTPS saat demo.

## Urutan kerja yang disarankan
1. B0 mock: fungsi dengan tanda tangan sama seperti `kcrypto/api.py` (boleh tidak mengenkripsi), supaya semua endpoint bisa dibuat dulu.
2. B1 DB, B2 auth, B3 otorisasi, lalu tulis tes IDOR **sebelum** menambah endpoint data.
3. Setelah A6 selesai: ganti mock dengan `kcrypto` asli (B5).
4. Terakhir audit log, TLS, dan tes keamanan.

## Struktur `app/` (usulan)
`main.py` (aplikasi dan routing), `config.py`, `db.py`, `models.py`, `auth.py`, `deps.py` (dependency otorisasi),
`items.py`, `audit.py`, `storage.py`. Tes di `tests/`.
