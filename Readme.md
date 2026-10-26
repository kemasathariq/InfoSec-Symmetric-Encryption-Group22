# Mobile Banking (tahap 2: frontend; enkripsi belum aktif)

Flask + SQLite. Fokus: pendaftaran (data pribadi + KTP + dokumen kantor + video selfie), login, dan
pengambilan kembali data milik sendiri.

Antarmuka web tersedia di `http://127.0.0.1:5000/` setelah server dijalankan. Frontend disajikan
oleh Flask dan menggunakan endpoint API di bawah; tidak memerlukan layanan frontend terpisah.
Enkripsi belum aktif pada tahap ini, sesuai status hook backend.

Landing page editorial Lumio tersedia di `http://127.0.0.1:5000/lumio` sebagai halaman visual terpisah.

## Antarmuka web
- Buka rekening lewat formulir tiga langkah: data diri, unggah tiga dokumen, dan keamanan/persetujuan PDP.
- Masuk dengan email dan kata sandi, lalu lihat profil, saldo, nomor rekening, dan dokumen pribadi.
- Unduh dokumen melalui sesi aktif; backend memverifikasi SHA-256 sebelum mengirim file.
- Token sesi disimpan selama tab browser aktif dan dihapus saat logout.

## Jalankan
    pip install -r Requirements.txt
    python BE\App.py         # http://127.0.0.1:5000

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

## Tempat memasang enkripsi nanti
- `hooks.py`: `protect()` / `unprotect()` dipanggil untuk profil JSON dan setiap file. Isi dengan AES/DES/RC4.
- Kolom `cipher` di tabel `users` dan `documents` sudah ada (sekarang `none`) untuk mencatat cipher yang dipakai.
- Kolom `sha256` di `documents` = hash file asli, dipakai memverifikasi data kembali utuh setelah dekripsi.
- `email_lookup` dan `nik_lookup` (HMAC) dipakai untuk login/cek duplikat, jadi email & NIK di dalam
  profil bisa dienkripsi tanpa merusak pencarian.

## Catatan
- Password disimpan sebagai hash (werkzeug), bukan enkripsi simetris. Ini memang seharusnya begitu.
- Sebelum deploy: ganti `LOOKUP_KEY` (env var) dan pakai HTTPS.
- Penyimpanan file di disk memakai nama acak (`storage/<user_id>/<random>.bin`), nama asli ada di DB.