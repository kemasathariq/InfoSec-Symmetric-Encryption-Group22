# Kesepakatan Hari 0

Isi bersama dalam rapat pertama. Setiap baris harus punya keputusan sebelum anggota berpisah.

| # | Keputusan | Usulan | Keputusan final | Alasan |
|---|---|---|---|---|
| 1 | Skenario | telemedicine / klinik digital | _TODO_ | |
| 2 | Bahasa utama backend | Python | _TODO_ | |
| 3 | Framework backend | FastAPI | _TODO_ | |
| 4 | Frontend | React + Vite | _TODO_ | |
| 5 | Database | PostgreSQL (SQLite untuk dev) | _TODO_ | |
| 6 | Library kripto | PyCryptodome | _TODO_ | |
| 7 | Penyimpanan blob | filesystem (volume Docker) | _TODO_ | |
| 8 | Sesi | token di server-side session atau JWT pendek | _TODO_ | |
| 9 | Ukuran chunk enkripsi | 1 MiB | _TODO_ | |
| 10 | Konvensi nama / branch | lihat CONTRIBUTING.md | _TODO_ | |

## Tafsir syarat "everything you store must be protected with each cipher"

_TODO (D): tulis tafsir yang dipilih dan alasannya. Usulan: setiap item disimpan sebagai 3 salinan
terenkripsi, satu per cipher. Catat konsekuensinya: 3× penyimpanan, 3× waktu upload, dan peluang
fitur verifikasi silang antar salinan._

## Kontrak yang dikunci hari ini

- [ ] Tanda tangan fungsi di `kcrypto/api.py`
- [ ] Format header file terenkripsi (`docs/04`)
- [ ] Daftar endpoint di `openapi.yaml`
- [ ] Daftar tabel dan kolom DB (`backend/README.md`)
