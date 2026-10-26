# PRD – Mobile Banking dengan Perlindungan Data Simetris

Versi 1.0 · 27 Oktober 2026 · Status: Draft · Tahap saat ini: 2 (frontend; enkripsi belum aktif)

## 1. Ringkasan

Produk ini adalah aplikasi web mobile banking sederhana untuk nasabah baru yang mendaftar secara digital (onboarding e-KYC). Saat mendaftar, nasabah mengunggah data pribadi, scan KTP, dokumen kantor (misalnya slip gaji), dan video selfie. Semua data itu sensitif, sehingga aplikasi harus menyimpannya dalam bentuk terlindungi dan hanya mengembalikannya, utuh, kepada pemiliknya yang sudah terautentikasi.

Aplikasi ini dibuat untuk tugas proyek implementasi enkripsi simetris (Assignment 1, kelompok 4 orang). Perlindungan data dilakukan dengan tiga cipher, yaitu AES, DES, dan RC4, lalu ketiganya dibandingkan secara terukur untuk skenario ini. Dokumen ini mencakup seluruh proyek. Tahap 1 (backend tanpa enkripsi) dan tahap 2 (frontend web) sudah selesai; enkripsi dan evaluasi dikerjakan bertahap.

## 2. Latar belakang dan skenario

**Skenario yang dipilih:** bank digital yang menerima pendaftaran nasabah sepenuhnya lewat aplikasi, tanpa datang ke cabang.

**Mengapa perlindungan data penting di sini:**

- Satu berkas pendaftaran memuat identitas lengkap (NIK, nama, alamat, tanggal lahir, foto KTP) dan bukti penghasilan. Kombinasi ini cukup untuk pencurian identitas dan pengajuan pinjaman palsu.
- Video selfie adalah data biometrik. Jika bocor, nasabah tidak bisa "mengganti" wajahnya.
- Basis data dan penyimpanan file adalah target utama kebocoran. Jika penyerang mendapat salinan disk atau database, data yang terenkripsi harus tetap tidak terbaca.
- Regulasi (UU PDP No. 27 Tahun 2022 dan GDPR) mewajibkan pengendali data menjaga kerahasiaan dan integritas data pribadi.

**Mengapa aplikasi ini berguna:** nasabah bisa mendaftar dari ponsel, sedangkan data kiriman mereka tetap tidak terbaca oleh siapa pun yang hanya memiliki akses ke penyimpanan, dan hanya bisa diambil kembali oleh pemiliknya.

## 3. Tujuan dan non-tujuan

### Tujuan

1. Menyediakan alur pendaftaran nasabah yang lengkap (data pribadi, KTP, dokumen kantor, video).
2. Menyimpan semua data privat dalam bentuk terlindungi dengan AES, DES, dan RC4, memakai mode operasi yang sesuai (bukan ECB).
3. Memastikan hanya pengguna terautentikasi yang dapat mengambil datanya sendiri, dan data kembali utuh (terbukti lewat verifikasi hash).
4. Mengevaluasi ketiga cipher secara terukur dan menafsirkan hasilnya untuk skenario ini.
5. Mendokumentasikan setiap keputusan desain penting beserta alasannya.

### Non-tujuan

- Fitur perbankan penuh (transfer, mutasi, pembayaran, kartu).
- Verifikasi KTP otomatis (OCR, face matching, liveness detection).
- Kepatuhan OJK atau PCI-DSS penuh.
- Skalabilitas produksi (load balancing, replikasi database).
- Aplikasi mobile native. Yang dibuat adalah web app.

## 4. Pengguna

| Peran | Deskripsi | Kebutuhan utama |
| --- | --- | --- |
| Calon nasabah / nasabah | Individu usia 17 tahun ke atas yang mendaftar dan login dari ponsel | Mendaftar dengan mudah, yakin datanya aman, dapat mengambil kembali dokumennya |
| Penyerang (ancaman) | Pihak dengan akses ke disk, salinan database, atau akun nasabah lain | Membaca atau mengambil data nasabah lain |
| Tim pengembang / penilai | Mahasiswa dan dosen | Kode yang bisa diverifikasi, alasan desain jelas, hasil evaluasi bermakna |

Tidak ada peran admin pada lingkup proyek ini.

## 5. Klasifikasi data

Keputusan data mana yang dianggap privat didasarkan pada UU PDP dan GDPR. Pada UU PDP, data biometrik dan data keuangan pribadi termasuk data pribadi yang bersifat spesifik. Pada GDPR, biometrik untuk identifikasi termasuk kategori khusus. Rujukan pasal sebaiknya diverifikasi ulang tim sebelum masuk laporan.

| Data | Kategori | Privat? | Alasan | Perlakuan |
| --- | --- | --- | --- | --- |
| Nama lengkap, NIK, alamat, tanggal lahir | Data pribadi umum, dapat mengidentifikasi | Ya | Identitas langsung; NIK adalah kunci identitas nasional | Dienkripsi (profil JSON) |
| Email, nomor HP | Data pribadi umum | Ya | Dapat dipakai untuk menghubungi dan menipu nasabah | Dienkripsi di profil; pencarian lewat HMAC |
| Scan KTP | Dokumen identitas | Ya | Memuat NIK, foto, dan data pribadi lain | Dienkripsi |
| Dokumen kantor (slip gaji, dsb.) | Data keuangan pribadi (spesifik) | Ya | Mengungkap penghasilan dan tempat kerja | Dienkripsi |
| Video selfie | Biometrik (spesifik) | Ya | Tidak dapat diganti jika bocor | Dienkripsi |
| Password | Kredensial | Ya | Tidak boleh pernah dibaca kembali | Hash (bukan enkripsi simetris) |
| Nomor rekening, saldo | Data keuangan | Ya | Terkait langsung dengan harta nasabah | Dilindungi akses; enkripsi opsional (lihat pertanyaan terbuka) |
| Waktu persetujuan, metadata file | Metadata | Tidak (risiko rendah) | Tidak mengidentifikasi sendirian | Disimpan apa adanya |

Prinsip yang dipakai: pengumpulan data seperlunya, persetujuan eksplisit (`consent_pdp`) dicatat dengan waktunya, dan data hanya dikembalikan kepada pemiliknya.

## 6. Kebutuhan fungsional

| ID | Kebutuhan | Prioritas | Status |
| --- | --- | --- | --- |
| FR-1 | Pendaftaran dengan data pribadi, password, dan persetujuan PDP | Wajib | Selesai |
| FR-2 | Unggah tiga file wajib: KTP (jpg/png/pdf), dokumen kantor (pdf/doc/docx/xls/xlsx), video selfie (mp4/webm/mov) | Wajib | Selesai |
| FR-3 | Validasi input: NIK 16 digit, format email, nomor HP Indonesia, usia minimal 17 tahun, password minimal 8 karakter, ekstensi file | Wajib | Selesai |
| FR-4 | Tolak pendaftaran ganda (email atau NIK sama) | Wajib | Selesai |
| FR-5 | Pembuatan nomor rekening otomatis saat daftar | Wajib | Selesai |
| FR-6 | Login dengan email dan password, menghasilkan token sesi (berlaku 24 jam) | Wajib | Selesai |
| FR-7 | Logout yang menghapus sesi | Wajib | Selesai |
| FR-8 | Lihat profil, rekening, dan daftar dokumen milik sendiri | Wajib | Selesai |
| FR-9 | Unduh dokumen milik sendiri dengan verifikasi integritas SHA-256 | Wajib | Selesai |
| FR-10 | Pendaftaran bersifat atomik: jika ada langkah gagal, data dan file yang sudah tertulis dibatalkan | Wajib | Selesai |
| FR-11 | Enkripsi semua profil dan file dengan AES, DES, dan RC4 | Wajib | Rencana (tahap 3–4) |
| FR-12 | Dekripsi saat pemilik mengambil data, dan hash cocok dengan aslinya | Wajib | Rencana |
| FR-13 | Antarmuka web: form pendaftaran multi-langkah, login, halaman profil dan dokumen | Wajib | Rencana (tahap 2) |
| FR-14 | Skrip benchmark untuk membandingkan ketiga cipher | Wajib | Rencana (tahap 5) |

## 7. Kebutuhan non-fungsional

| Aspek | Kebutuhan |
| --- | --- |
| Keamanan | Tidak ada mode ECB. Password di-hash. Token sesi disimpan sebagai hash. Akses data selalu dibatasi user\_id dari sesi. |
| Integritas | Setiap file punya SHA-256 asli; unduhan ditolak jika hash tidak cocok. |
| Kinerja | Pendaftaran dengan total unggahan hingga 60 MB selesai dalam waktu wajar di laptop biasa; angka target ditetapkan setelah benchmark. |
| Keterbacaan | Kode ringkas, titik enkripsi terpusat di `hooks.py` agar mudah dijelaskan di laporan. |
| Portabilitas | Berjalan lokal dengan Python dan Flask, tanpa layanan eksternal. |
| Keterlacakan | Riwayat commit GitHub rutin dan bermakna; percakapan AI dilampirkan. |

## 8. Arsitektur dan keputusan desain

Arsitektur tahap 1: klien (web) memanggil API JSON/multipart di Flask. Flask menyimpan metadata dan profil di SQLite, dan menyimpan file di direktori `storage/<user_id>/`. Semua data privat melewati `hooks.protect()` sebelum ditulis dan `hooks.unprotect()` setelah dibaca.

Setiap keputusan penting dicatat dengan alasannya, karena soal menuntut justifikasi (alasan "paling mudah" tidak diterima).

| Keputusan | Alasan |
| --- | --- |
| Flask + SQLite | Cukup untuk skala tugas, tanpa server database terpisah, dan mudah direproduksi penilai. Batasannya (satu penulis sekaligus) tidak berpengaruh pada skenario ini. |
| Satu titik `protect/unprotect` | Mencegah ada data privat yang lolos tanpa enkripsi, dan memungkinkan pergantian cipher tanpa mengubah route. Mendukung evaluasi yang adil karena semua cipher memakai jalur kode yang sama. |
| Profil disimpan sebagai satu blob JSON | Satu operasi enkripsi per nasabah, bukan satu per kolom. Lebih sederhana dan lebih sedikit overhead IV/nonce. Konsekuensinya, field profil tidak bisa di-query di SQL, dan itu memang tidak diperlukan. |
| `email_lookup` dan `nik_lookup` berupa HMAC-SHA256 dengan kunci server | Login dan cek duplikat tetap bisa dilakukan setelah email/NIK dienkripsi. HMAC (bukan hash polos) mencegah penebakan NIK yang ruang nilainya kecil. |
| File disimpan dengan nama acak, nama asli di database | Nama berkas bisa membocorkan identitas; nama acak menghindarinya. |
| SHA-256 file asli disimpan | Membuktikan syarat "kembali utuh" setelah dekripsi. |
| Password di-hash (werkzeug), bukan dienkripsi | Password tidak pernah perlu dibaca kembali; hash satu arah adalah praktik yang benar. |
| Token sesi acak, hanya hash-nya disimpan | Jika tabel sesi bocor, token tidak bisa langsung dipakai. |
| Batas unggahan 60 MB | Membatasi memori karena file diproses utuh di memori; cukup untuk video selfie pendek. |
| Pendaftaran atomik | Menghindari data setengah jadi dan file yatim jika terjadi kegagalan. |

## 9. Spesifikasi API

| Method | Path | Auth | Fungsi |
| --- | --- | --- | --- |
| GET | /api/health | Tidak | Cek layanan |
| POST | /api/register | Tidak | Daftar (multipart: data pribadi, `consent_pdp`, file `ktp`, `supporting_doc`, `selfie_video`). Respons 201 berisi nomor rekening; 422 untuk validasi gagal; 409 untuk duplikat |
| POST | /api/login | Tidak | JSON `{email, password}`, respons token; 401 jika salah |
| POST | /api/logout | Bearer | Hapus sesi |
| GET | /api/me | Bearer | Profil, rekening, daftar dokumen |
| GET | /api/me/documents/{ktp, supporting\_doc, selfie\_video} | Bearer | Unduh file milik sendiri; 404 jika tidak ada; 500 jika integritas gagal |

## 10. Model data

- **users**: id, email\_lookup, nik\_lookup, password\_hash, profile (blob), cipher, account\_number, balance, consent\_at, created\_at.
- **documents**: id, user\_id, kind, original\_name, mime, path, size, sha256, cipher, created\_at. Unik per (user\_id, kind).
- **sessions**: token\_hash, user\_id, expires\_at.

Kolom `cipher` mencatat algoritma yang dipakai untuk setiap baris, sehingga data dari beberapa cipher bisa hidup berdampingan saat evaluasi.

## 11. Rencana enkripsi

Usulan awal berikut perlu dikonfirmasi dan dijustifikasi di laporan. Tidak ada yang memakai ECB.

| Cipher | Mode usulan | IV / nonce | Integritas | Catatan |
| --- | --- | --- | --- | --- |
| AES-256 | GCM (alternatif: CTR atau CBC) | Nonce acak 96-bit per objek | Tag autentikasi bawaan GCM | Pilihan utama; mode terautentikasi menjaga kerahasiaan sekaligus integritas |
| DES | CBC | IV acak 64-bit per objek | HMAC-SHA256 (encrypt-then-MAC) | Kunci efektif 56-bit, sudah tidak aman; dipakai untuk perbandingan, bukan rekomendasi. Padding PKCS7 diperlukan |
| RC4 | Stream cipher (tanpa mode) | Tidak punya IV; turunkan kunci per objek dari kunci utama + salt acak (misalnya HKDF) agar keystream tidak berulang | HMAC-SHA256 (encrypt-then-MAC) | Diketahui memiliki bias keystream; dipakai untuk perbandingan |

Manajemen kunci tahap awal: kunci utama dari environment variable, kunci per pengguna/objek diturunkan dengan KDF memakai `user_id` dan `purpose` yang sudah tersedia pada `hooks.py`. Cara ini perlu dibahas ulang di laporan, termasuk risiko menyimpan kunci di server yang sama dengan datanya.

Format tersimpan per objek: `cipher_id | salt | iv/nonce | ciphertext | tag/MAC`, supaya dekripsi tidak butuh informasi di luar blob selain kunci utama.

## 12. Rencana evaluasi

Pertanyaan yang dijawab: cipher mana yang paling cocok untuk data pendaftaran nasabah, dan seberapa besar bedanya dalam praktik?

**Yang diukur**

| Metrik | Alasan relevan untuk skenario |
| --- | --- |
| Waktu enkripsi dan dekripsi per ukuran objek | Menentukan lama pendaftaran dan unduhan dokumen |
| Throughput (MB/s) | Penting untuk video berukuran puluhan MB |
| Penggunaan memori puncak | Server memproses file utuh di memori |
| Overhead ukuran ciphertext | Dampak ke penyimpanan (padding, IV, tag) |
| Ketepatan round-trip (hash cocok) | Syarat "kembali utuh" |

**Cara mengukur secara andal**

- Ukuran uji mewakili data nyata: profil JSON (\~1 KB), scan KTP (\~500 KB), dokumen kantor (\~2 MB), video (\~20–50 MB).
- Pustaka, mesin, dan kondisi sama untuk ketiga cipher; ada pemanasan (warm-up) sebelum pengukuran.
- Minimal 30 pengulangan per kombinasi; laporkan median dan simpangan baku (atau persentil), bukan satu angka.
- Pisahkan biaya penyiapan kunci dari biaya enkripsi data.
- Data uji acak dan data yang dapat dikompresi diuji sama-sama agar tidak bias.

**Cara menafsirkan.** Hasil dihubungkan ke skenario, misalnya apakah selisih waktu pada file 500 KB terasa bagi nasabah, apakah video memerlukan pemrosesan per-potongan (chunk), dan apakah kecepatan DES atau RC4 sebanding dengan hilangnya keamanan. Angka tanpa tafsir tidak akan dimasukkan ke laporan.

## 13. Keamanan dan privasi

**Model ancaman dalam lingkup**

- Penyerang mendapat salinan database atau direktori `storage/`: data harus tidak terbaca.
- Nasabah terautentikasi mencoba mengambil data nasabah lain: ditolak karena query dibatasi `user_id` sesi.
- File rusak atau dimodifikasi di disk: terdeteksi lewat verifikasi hash dan MAC.

**Di luar lingkup tahap ini:** serangan jaringan (diasumsikan HTTPS saat dipakai sungguhan), rate limiting dan proteksi brute force, pemulihan akun, pencabutan persetujuan dan penghapusan data (hak subjek data), serta perlindungan kunci utama di server yang sudah dikompromi.

**Keterbatasan yang diketahui saat ini:** belum ada HTTPS, rate limiting, pemeriksaan isi file (hanya ekstensi), maupun audit log. Hal ini akan dicantumkan jujur di laporan.

## 14. Kriteria penerimaan

1. Pendaftaran dengan data valid dan tiga file berhasil, dan nomor rekening dikembalikan.
2. Input tidak valid mengembalikan 422 dengan pesan per-field. Email atau NIK duplikat mengembalikan 409.
3. Pengguna tanpa token atau dengan token kedaluwarsa tidak bisa mengakses `/api/me` maupun dokumen.
4. File yang diunduh identik byte demi byte dengan yang diunggah.
5. Setelah enkripsi aktif: isi `storage/` dan kolom `profile` tidak mengandung data polos, tidak ada ECB, dan dekripsi menghasilkan data identik untuk ketiga cipher.
6. Hasil benchmark dilengkapi tafsiran yang mengaitkannya dengan skenario.

## 15. Rencana kerja

| Tahap | Isi | Status |
| --- | --- | --- |
| 1 | Backend Flask tanpa enkripsi (registrasi, login, profil, unduh dokumen, hook enkripsi) | Selesai |
| 2 | Frontend web (form pendaftaran multi-langkah, login, profil, dokumen) | Selesai |
| 3 | Implementasi AES di `hooks.py` beserta uji round-trip | Rencana |
| 4 | Implementasi DES dan RC4, pemilihan cipher lewat konfigurasi | Rencana |
| 5 | Skrip benchmark, pengumpulan data, analisis | Rencana |
| 6 | Laporan maksimal 2 halaman A4, rapikan README | Rencana |

## 16. Deliverable dan ketentuan pengumpulan

- Seluruh kode di GitHub dengan commit teratur dan bermakna (riwayat commit ikut dinilai).
- Laporan maksimal 2 halaman A4: skenario dan kegunaannya, analisis yang dipilih beserta alasannya, dan justifikasi setiap keputusan desain penting.
- Tautan percakapan AI beserta tangkapan layarnya.
- Semua isi laporan dan kode harus dipahami dan dapat dipertanggungjawabkan oleh anggota tim. Konten AI yang tidak diverifikasi berisiko nilai 0.

## 17. Risiko

| Risiko | Dampak | Mitigasi |
| --- | --- | --- |
| Skenario dianggap terlalu generik | Ditolak | Tekankan alur onboarding e-KYC dan klasifikasi data berdasarkan UU PDP/GDPR |
| Salah memilih atau menerapkan mode operasi (IV dipakai ulang, tanpa MAC) | Enkripsi lemah, nilai turun | Format blob baku, nonce acak per objek, uji otomatis |
| Video besar memenuhi memori | Server lambat atau gagal | Batas 60 MB; pertimbangkan pemrosesan per-chunk |
| Hasil benchmark tidak stabil | Kesimpulan lemah | Pengulangan, pemanasan, median dan simpangan baku |
| Penggunaan AI tanpa verifikasi | Nilai 0 | Setiap anggota meninjau kode dan memahami alasannya; simpan log percakapan |
| Pembagian kerja tidak merata | Riwayat commit timpang | Tetapkan pemilik tiap tahap; commit kecil dan rutin |

## 18. Pertanyaan terbuka

1. Soal menyebut data harus dilindungi "dengan masing-masing cipher: AES, DES, RC4". Apakah artinya sistem mendukung ketiganya secara bergantian (dipilih per data), atau setiap data dienkripsi berlapis oleh ketiganya? Perlu dikonfirmasi ke dosen sebelum tahap 3.
2. Apakah nomor rekening dan saldo ikut dienkripsi atau cukup dilindungi kontrol akses?
3. Apakah AES-GCM dapat diterima sebagai "mode operasi yang sesuai", atau dosen mengharapkan mode klasik (CBC/CTR) dengan MAC terpisah?
4. Pustaka kriptografi yang dipakai: pustaka siap pakai (misalnya `cryptography`, `pycryptodome`) atau implementasi sendiri? Soal membolehkan pustaka apa pun.
5. Bagaimana kunci utama dikelola selama pengembangan dan demo?
