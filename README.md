# Mobile Banking dengan Perlindungan Data Simetris (AES / DES / RC4)

Flask + SQLite. Fokus: pendaftaran (data pribadi + KTP + dokumen kantor + video selfie), login, dan
pengambilan kembali data milik sendiri.

Antarmuka web tersedia di `http://127.0.0.1:5000/` setelah server dijalankan. Frontend disajikan
oleh Flask dan menggunakan endpoint API di bawah; tidak memerlukan layanan frontend terpisah.
Enkripsi belum aktif pada tahap ini, sesuai status hook backend.

## Antarmuka web
- Buka rekening lewat formulir tiga langkah: data diri, unggah tiga dokumen, dan keamanan/persetujuan PDP.
- Masuk dengan email dan kata sandi, lalu lihat profil, saldo, nomor rekening, dan dokumen pribadi.
- Unduh dokumen melalui sesi aktif; backend memverifikasi SHA-256 sebelum mengirim file.
- Token sesi disimpan selama tab browser aktif dan dihapus saat logout.

## Jalankan
    pip install -r requirements.txt
    python BE/App.py         # http://127.0.0.1:5000

## Endpoint
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| POST | /api/register | - | multipart: full_name, nik, email, phone, date_of_birth (YYYY-MM-DD), address, password, consent_pdp=true, file: ktp, supporting_doc, selfie_video |
| POST | /api/login | - | JSON {email, password} -> token |
| GET  | /api/me | Bearer | profil, nomor rekening, daftar dokumen |
| GET  | /api/me/documents/<ktp\|supporting_doc\|selfie_video> | Bearer | unduh file milik sendiri (dicek SHA-256) |
| POST | /api/logout | Bearer | hapus sesi |

## Contoh curl
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
- `BE/Hooks.py`: `protect()` / `unprotect()` untuk profil JSON dan setiap file. Tiap jenis data punya cipher sendiri (profil dan video AES, dokumen RC4, KTP DES). Ubah dengan `CIPHER_POLICY`, paksa satu cipher dengan `CIPHER=aes|des|rc4`, atau pakai ketiganya berlapis (AES lalu DES lalu RC4) dengan `CIPHER=layered`.
- `BE/ciphers.py`: AES-256-GCM, DES-CTR + HMAC-SHA256, RC4 (drop 3072) + HMAC-SHA256. Kunci per objek dari `MASTER_KEY` via HKDF. Tanpa ECB.
- Kolom `cipher` mencatat cipher, `sha256` memverifikasi data kembali utuh.
- `email_lookup` dan `nik_lookup` (HMAC) untuk login dan cek duplikat.

## Dokumen
- `docs/DATA_CLASSIFICATION.md`: data privat menurut UU PDP dan GDPR.
- `docs/CRYPTO_DESIGN.md`: desain, pemilihan mode, hasil benchmark.
- `docs/HANDOFF_BRILIAN.md`: tugas backend, DB, deploy.

## Uji dan benchmark
    python -m unittest discover -s tests
    python bench/benchmark.py          # bench/results.md|csv|png
    python bench/mode_comparison.py    # bench/modes.md

## Catatan
- Password disimpan sebagai hash (werkzeug), bukan enkripsi simetris. Ini memang seharusnya begitu.
- Sebelum deploy: set `MASTER_KEY` dan `LOOKUP_KEY` (acak, berbeda), matikan `debug`, pakai HTTPS.
- Penyimpanan file di disk memakai nama acak (`storage/<user_id>/<random>.bin`), nama asli ada di DB.
