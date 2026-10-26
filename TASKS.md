# Daftar Tugas

Status: `[ ]` belum, `[~]` berjalan, `[x]` selesai. Perbarui lewat PR kecil.
**Bergantung** = tugas lain yang harus selesai (atau di-mock) dulu.

## Bersama (hari 0)

| ID | Tugas | Pemilik | Status |
|---|---|---|---|
| H0-1 | Finalkan skenario dan daftar jenis data (`docs/01`) | semua | [ ] |
| H0-2 | Tetapkan stack, versi, dan library (`docs/00`) | semua | [ ] |
| H0-3 | Sepakati kontrak: `kcrypto/api.py`, format header, `openapi.yaml`, daftar tabel DB | semua | [ ] |
| H0-4 | Buat repo, branch `main` dilindungi, aturan PR | C | [ ] |
| H0-5 | Tulis tafsir "3 salinan" dan alasannya (`docs/00`) | D | [ ] |

## A: Cryptography Engineer (`kcrypto/`)

| ID | Tugas | Minggu | Bergantung | Status |
|---|---|---|---|---|
| A1 | Rancang format file terenkripsi + header (`docs/04`) | 1 | H0-3 | [ ] |
| A2 | AES-256-GCM, chunked | 1 | A1 | [ ] |
| A3 | DES-CBC + HMAC (encrypt-then-MAC) | 1 | A1 | [ ] |
| A4 | RC4 + HMAC, kunci unik per chunk | 1 | A1 | [ ] |
| A5 | Manajemen kunci: Argon2id, wrap/unwrap, HKDF | 1 | H0-3 | [ ] |
| A6 | Antarmuka seragam `api.py` + helper 3 salinan + verifikasi | 1 | A2-A5 | [ ] |
| A7 | Unit test: round-trip, tamper, test vector | 1-2 | A2-A6 | [ ] |
| A8 | Uji file besar (video): memori tetap rendah | 2 | A6 | [ ] |
| A9 | Review keamanan kode backend (bantu B) | 3 | B5 | [ ] |
| A10 | Tulis bab "Desain kripto" | 3 | A7 | [ ] |

## B: Backend & Security Engineer (`backend/`)

| ID | Tugas | Minggu | Bergantung | Status |
|---|---|---|---|---|
| B0 | Mock modul kripto (agar tidak menunggu A) | 1 | H0-3 | [ ] |
| B1 | Skema DB + migrasi | 1 | H0-3 | [ ] |
| B2 | Registrasi, login, hash password, sesi/JWT, rate limit, lockout | 1 | B1 | [ ] |
| B3 | Otorisasi: hanya pemilik, anti-IDOR | 1 | B2 | [ ] |
| B4 | Endpoint data pribadi (profil) | 1-2 | B3, B0 | [ ] |
| B5 | Upload (3 salinan) + download streaming (+ Range untuk video) | 2 | B3, A6 | [ ] |
| B6 | Endpoint verifikasi 3 salinan | 2 | B5 | [ ] |
| B7 | Audit log (append-only, hash-chained) | 2 | B1 | [ ] |
| B8 | HTTPS/TLS, header keamanan | 2-3 | C7 | [ ] |
| B9 | Tes keamanan backend (IDOR, tamper di storage, brute force) | 3 | B5 | [ ] |
| B10 | Tulis bab "Arsitektur dan keamanan aplikasi" | 3 | B9 | [ ] |

## C: Frontend & Integration Engineer (`frontend/`, `scripts/`)

| ID | Tugas | Minggu | Bergantung | Status |
|---|---|---|---|---|
| C1 | Wireframe dan alur pasien | 1 | H0-1 | [ ] |
| C2 | Halaman registrasi/login | 1 | openapi | [ ] |
| C3 | Form data pribadi | 1 | openapi | [ ] |
| C4 | Upload KTP / dokumen / video + indikator progres | 1-2 | openapi | [ ] |
| C5 | Dashboard "data saya": daftar, unduh, pilih algoritma, tombol verifikasi | 2 | B5, B6 | [ ] |
| C6 | Pemutar video | 2 | B5 | [ ] |
| C7 | `docker-compose.yml` (api, db, frontend, proxy TLS) | 1-2 | stack | [ ] |
| C8 | Data dummy + video demo (`scripts/`) | 1 | H0-1 | [ ] |
| C9 | Tes E2E termasuk uji negatif | 2-3 | B5 | [ ] |
| C10 | Tulis bab "Implementasi dan deployment" + naskah demo | 3 | C9 | [ ] |

## D: Analyst & Benchmark Engineer (`docs/`, `bench/`)

| ID | Tugas | Minggu | Bergantung | Status |
|---|---|---|---|---|
| D1 | Analisis UU PDP dan GDPR, tabel klasifikasi (`docs/02`), cek pasal ke teks resmi | 1 | H0-1 | [ ] |
| D2 | Threat model (`docs/03`) | 1 | H0-1 | [ ] |
| D3 | Rancang metodologi benchmark (`docs/05`) | 1 | H0-3 | [ ] |
| D4 | Implementasi harness + varian uji | 1-2 | D3 | [ ] |
| D5 | Dataset uji (4 kelas ukuran) | 1 | D3 | [ ] |
| D6 | Jalankan benchmark penuh + catat spesifikasi mesin | 2 | D4, A6 | [ ] |
| D7 | Analisis statistik + grafik | 2-3 | D6 | [ ] |
| D8 | **Interpretasi tertulis** (mengapa hasilnya begitu; apa artinya untuk skenario) | 3 | D7 | [ ] |
| D9 | Uji negatif bersama C | 2-3 | B5 | [ ] |
| D10 | Susun laporan akhir dan slide | 3 | semua bab | [ ] |
