# Mobile Banking dengan Perlindungan Data Simetris (AES / DES / RC4)

Aplikasi web pendaftaran nasabah bank digital (e-KYC) untuk tugas Keamanan Informasi, Kelompok 22.
Nasabah mendaftar dengan data pribadi, scan KTP, dokumen kantor (slip gaji), dan video selfie. Semua
data privat dienkripsi sebelum disimpan, dan hanya bisa diambil kembali, utuh, oleh pemiliknya yang
sudah login.

- **Stack:** Python, Flask, SQLite, pycryptodome. Frontend disajikan oleh Flask yang sama.
- **Aplikasi online:** _[isi link deploy di sini]_

## Menjalankan di komputer sendiri

Butuh Python 3.10 atau lebih baru. Jalankan dari folder root repo.

**1. Pasang dependensi**

    python -m venv .venv
    .venv\Scripts\Activate.ps1          # Windows PowerShell
    source .venv/bin/activate           # macOS / Linux
    pip install -r requirements.txt

**2. Buat file `.env` dan isi dua kunci**

    copy .env.example .env              # Windows
    cp .env.example .env                # macOS / Linux
    python -c "import secrets; print(secrets.token_hex(32))"

Jalankan perintah terakhir dua kali. Tempel hasil pertama ke `MASTER_KEY=` dan hasil kedua ke
`LOOKUP_KEY=` di `.env`. Aplikasi **menolak berjalan** kalau salah satu kunci kosong atau keduanya
sama, supaya tidak pernah memakai kunci bawaan. `.env` tidak boleh di-commit (sudah ada di
`.gitignore`).

Simpan `MASTER_KEY` baik-baik. Kalau kunci ini hilang atau diganti, semua data yang sudah tersimpan
tidak bisa dibaca lagi. Untuk mulai dari awal, hapus `BE/mbanking.db` dan folder `BE/storage`.

**3. Jalankan**

    python BE/App.py                    # http://127.0.0.1:5000

Mode debug mati secara default. Untuk mengembangkan, set `FLASK_DEBUG=1`. Jangan nyalakan debug di
server publik, karena debugger Flask bisa dipakai untuk menjalankan kode.

## Menjalankan di server (produksi)

    gunicorn --chdir BE App:app --workers 1 --timeout 120 --bind 0.0.0.0:$PORT

- Set `MASTER_KEY`, `LOOKUP_KEY`, dan `APP_ENV=production` di pengaturan secret host, bukan di file.
- `DB_PATH` dan `STORAGE_DIR` harus berada di disk yang tidak hilang saat restart (volume).
  Host serverless seperti Vercel tidak cocok.
- Gunakan HTTPS (disediakan host).
- Setiap unggahan diproses utuh di memori, sekitar 3-4x ukuran unggahan (maksimal 60 MB). Sesuaikan
  jumlah worker dengan RAM server.
- gunicorn tidak berjalan di Windows. Di Windows cukup pakai `python BE/App.py` untuk pengujian lokal.

## Pengaturan (`.env` atau environment variable)

| Nama | Wajib | Fungsi |
|---|---|---|
| `MASTER_KEY` | Ya | Akar semua kunci enkripsi (kunci per objek diturunkan dengan HKDF) |
| `LOOKUP_KEY` | Ya | Kunci HMAC untuk mencari email dan NIK tanpa menyimpannya polos. Harus berbeda dari `MASTER_KEY` |
| `CIPHER` | Tidak | `aes`, `des`, atau `rc4` untuk semua data, atau `layered` (AES lalu DES lalu RC4 pada setiap item). Kosong = satu cipher per jenis data (lihat di bawah) |
| `CIPHER_POLICY` | Tidak | Ganti cipher per jenis data, misalnya `ktp=aes,supporting_doc=aes` |
| `DB_PATH`, `STORAGE_DIR` | Tidak | Lokasi database dan file terenkripsi. Path relatif dihitung dari root repo |
| `FLASK_DEBUG` | Tidak | `1` untuk menyalakan mode debug saat pengembangan |
| `APP_ENV` | Tidak | `production` di server |

Mengganti `CIPHER` tidak merusak data lama, karena setiap item menyimpan cipher yang dipakainya.

## Antarmuka web

- Buka rekening lewat formulir tiga langkah: data diri, unggah tiga dokumen, lalu kata sandi dan
  persetujuan pemrosesan data (UU PDP).
- Masuk dengan email dan kata sandi, lalu lihat profil (NIK ditampilkan tersamar), nomor rekening,
  saldo, dan dokumen.
- Unduh dokumen milik sendiri. File didekripsi, diperiksa SHA-256-nya, lalu dikirim dengan nama generik
  (`ktp.jpg`, `supporting_doc.pdf`, `selfie_video.mp4`).
- Token sesi disimpan selama tab browser terbuka dan dihapus saat logout.

## Endpoint API

| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | /api/health | - | Cek layanan |
| POST | /api/register | - | multipart: `full_name`, `nik`, `email`, `phone`, `date_of_birth` (YYYY-MM-DD), `address`, `password`, `consent_pdp=true`, file `ktp`, `supporting_doc`, `selfie_video`. 201 + nomor rekening; 422 validasi gagal (pesan per kolom); 409 email atau NIK sudah terdaftar; 413 total unggahan > 60 MB |
| POST | /api/login | - | JSON `{email, password}`. 200 + token (berlaku 24 jam); 401 email atau password salah |
| GET | /api/me | Bearer | Profil, nomor rekening, saldo, daftar dokumen |
| GET | /api/me/documents/<ktp\|supporting_doc\|selfie_video> | Bearer | Unduh file milik sendiri. 404 kalau tidak ada; 500 kalau data rusak atau diubah (pemeriksaan integritas gagal) |
| POST | /api/logout | Bearer | Hapus sesi |

Error dari endpoint di atas dikembalikan sebagai JSON `{"error": "..."}`.

## Contoh curl

Contoh untuk bash. Di PowerShell, pakai `curl.exe` dan ganti `\` di akhir baris dengan `` ` ``.

    curl -X POST localhost:5000/api/register \
      -F full_name="Budi Santoso" -F nik=3578012345670001 -F email=budi@mail.com \
      -F phone=08123456789 -F date_of_birth=2000-05-01 -F address="Jl. Raya No. 1 Surabaya" \
      -F password=rahasia123 -F consent_pdp=true \
      -F ktp=@ktp.jpg -F supporting_doc=@slip.pdf -F selfie_video=@selfie.mp4

    curl -X POST localhost:5000/api/login -H "Content-Type: application/json" \
      -d '{"email":"budi@mail.com","password":"rahasia123"}'

    curl localhost:5000/api/me -H "Authorization: Bearer <token>"
    curl -OJ localhost:5000/api/me/documents/ktp -H "Authorization: Bearer <token>"

## Enkripsi

- `BE/Hooks.py`: `protect()` / `unprotect()`, satu-satunya jalan data privat masuk dan keluar dari
  penyimpanan. Bawaannya satu cipher per jenis data: profil dan video AES, dokumen kantor RC4, KTP DES.
  Bisa diganti lewat `CIPHER` atau `CIPHER_POLICY`.
- `BE/ciphers.py`: AES-256-GCM, DES-CTR + HMAC-SHA256, RC4 (3072 byte pertama dibuang) +
  HMAC-SHA256. Tidak ada ECB. Setiap item punya kunci sendiri (HKDF dari `MASTER_KEY` dengan salt
  acak), dan tag-nya mengikat `user_id` serta jenis data, sehingga file yang dipindah ke pengguna
  lain gagal didekripsi.
- `BE/config.py`: membaca `.env` dan menghentikan aplikasi kalau kunci tidak ada.
- Alasan pemilihan mode dan hasil benchmark: `docs/CRYPTO_DESIGN.md`.

## Apa yang dienkripsi dan apa yang tidak

| Data | Perlakuan |
|---|---|
| Nama, NIK, tanggal lahir, alamat, email, nomor HP | Dienkripsi (profil JSON) |
| Scan KTP, dokumen kantor, video selfie | Dienkripsi, disimpan sebagai `storage/<user_id>/<nama acak>.bin` |
| Password | Di-hash (werkzeug), bukan dienkripsi, karena tidak perlu dibaca kembali |
| Email dan NIK untuk pencarian | HMAC-SHA256 dengan `LOOKUP_KEY` (`email_lookup`, `nik_lookup`) |
| Token sesi | Hanya hash-nya yang disimpan |
| Nama file asli | Tidak disimpan. Hanya ekstensinya (`.jpg`) |
| Nomor rekening, saldo | **Tidak dienkripsi.** Nomor rekening memang dibagikan untuk menerima transfer; saldo selalu 0 karena transaksi di luar lingkup |
| SHA-256 file asli, ukuran, jenis MIME, cipher, waktu | **Tidak dienkripsi** (metadata). SHA-256 dipakai untuk membuktikan file kembali utuh |

## Struktur repo

    BE/        App.py (route), DB.py (skema), Hooks.py, ciphers.py, config.py
    FE/        templates/index.html, static/js/app.js, static/css/app.css
    tests/     test_ciphers.py, test_app_e2e.py
    bench/     benchmark.py, mode_comparison.py, hasil (results.md|csv|png, modes.md)
    docs/      DATA_CLASSIFICATION.md, CRYPTO_DESIGN.md, HANDOFF_BRILIAN.md, REPORT_DRAFT.md

## Uji dan benchmark

    python -m unittest discover -s tests       # hasil yang benar: Ran 21 tests ... OK
    python bench/benchmark.py                  # bench/results.md|csv|png
    python bench/mode_comparison.py            # bench/modes.md

Tes mencakup round-trip ketiga cipher, deteksi perubahan setiap bit, pengikatan data ke pemilik,
alur lengkap lewat Flask untuk setiap cipher, kunci wajib, dan error JSON.

## Keterbatasan yang diketahui

- `MASTER_KEY` berada di server yang sama dengan data. Kalau server diretas, kuncinya ikut bocor.
- Belum ada pembatasan jumlah percobaan login dan pendaftaran (rate limiting).
- File diproses utuh di memori, belum per potongan (chunk).
- Isi file hanya dicek dari ekstensinya, belum dari isinya.
- Penghapusan data dan pencabutan persetujuan (hak subjek data UU PDP) belum dibuat.

## Dokumen lain

- `docs/DATA_CLASSIFICATION.md`: data privat menurut UU PDP dan GDPR.
- `docs/CRYPTO_DESIGN.md`: desain kriptografi, pemilihan mode, hasil dan tafsiran benchmark.
- `docs/HANDOFF_BRILIAN.md`: tugas backend, database, dan deploy.
