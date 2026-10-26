# KlinikKu: Penyimpanan Data Pasien Terenkripsi

Tugas 1 Keamanan Informasi (kelompok 4 orang).
**Status: kerangka awal. Belum ada implementasi.** Semua file `.py` hanya berisi kontrak dan daftar TODO.

## 1. Skenario (usulan, difinalkan di hari 0: lihat `docs/00-kesepakatan-hari-0.md`)

Platform telemedicine/klinik digital. Pengguna adalah **pasien**. Setiap pasien menyimpan data kesehatannya
dan hanya dirinya sendiri yang boleh mengambilnya kembali.

| Jenis data (syarat tugas) | Contoh di skenario |
|---|---|
| Data pribadi | nama, NIK, tanggal lahir, alamat, riwayat penyakit, alergi |
| Scan dokumen identitas | foto KTP / kartu BPJS |
| Dokumen kantor | surat rujukan (.docx), hasil lab (.pdf), resep (.xlsx) |
| Video | rekaman konsultasi / video gejala |

## 2. Syarat tugas dan di mana dipenuhi

| Syarat | Diwujudkan oleh | Dibuktikan oleh |
|---|---|---|
| Skenario konkret (bukan "file encryption service") | `docs/01-skenario.md` | semua |
| Menangani 4 jenis data | UI (C) + API (B) | demo + E2E test |
| Menentukan data privat berdasar GDPR / UU PDP | `docs/02-klasifikasi-data.md` (D) | tabel dengan pasal yang sudah dicek |
| **Semua data dilindungi AES, DES, dan RC4** | tiap item disimpan sebagai **3 salinan terenkripsi** (A + B) | tes: 3 salinan didekripsi dan hash-nya sama |
| Mode operasi bukan ECB | `docs/04-desain-kripto.md` (A) | tes + review kode |
| Hanya user terautentikasi bisa mengambil datanya sendiri, utuh | auth + otorisasi (B) | tes IDOR + hash sebelum/sesudah |
| Evaluasi perbandingan 3 cipher | `bench/` + `docs/05-benchmark-plan.md` (D) | laporan: angka + interpretasi |

Tafsir yang kami pakai untuk "everything you store must be protected with each of the ciphers":
**setiap item disimpan 3 kali, masing-masing dengan satu cipher.** (Tulis ulang alasannya di docs/00.)

## 3. Struktur repo

```
klinikku/
├── README.md             # dokumen ini
├── TASKS.md              # daftar tugas per orang + dependensi + status
├── CONTRIBUTING.md       # aturan Git
├── openapi.yaml          # KONTRAK API (kerangka; dilengkapi di hari 0 / minggu 1)
├── docker-compose.yml    # (C) kerangka
├── requirements.txt      # dependensi Python (daftar awal)
├── docs/                 # keputusan, regulasi, threat model, desain, rencana benchmark, laporan
├── kcrypto/              # (A) modul kripto           -> baca kcrypto/README.md
├── backend/              # (B) API, auth, DB, audit   -> baca backend/README.md
├── frontend/             # (C) antarmuka web          -> baca frontend/README.md
├── bench/                # (D) harness benchmark      -> baca bench/README.md
└── scripts/              # (C) pembuat data dummy
```

Nama paket kripto `kcrypto` (bukan `crypto`) supaya tidak tertukar dengan `Crypto` milik PyCryptodome.

## 4. Peran

| | Peran | Tanggung jawab inti | Folder |
|---|---|---|---|
| **A** | Cryptography Engineer | modul enkripsi, format file, manajemen kunci, tes kripto | `kcrypto/` |
| **B** | Backend & Security Engineer | autentikasi, otorisasi, DB, API, audit log, integritas | `backend/` |
| **C** | Frontend & Integration Engineer | UI, alur pasien, Docker, data dummy, tes E2E | `frontend/`, `scripts/`, `docker-compose.yml` |
| **D** | Analyst & Benchmark Engineer | regulasi, klasifikasi data, threat model, benchmark, laporan | `docs/`, `bench/` |

Setiap anggota juga menulis **bab laporan** sesuai perannya (lihat `docs/laporan/outline.md`).

## 5. Alur kerja dan milestone

| Fase | Tujuan | Selesai bila |
|---|---|---|
| **Hari 0** (rapat 1-2 jam, semua) | sepakati skenario, stack, kontrak antarmuka | `docs/00` terisi dan repo dibuat |
| **Minggu 1** (mandiri, paralel) | tiap modul jalan sendiri | A: tes kripto lolos. B: auth + DB dengan **mock** kripto. C: UI dengan mock API. D: tabel klasifikasi + kerangka harness |
| **Minggu 2** (integrasi) | sambungkan semua | upload > 3 salinan > login > download > hash sama, end-to-end. Benchmark penuh berjalan |
| **Minggu 3** (uji dan laporan) | uji negatif, perbaikan, laporan, latihan presentasi | semua kotak di bagian 7 tercentang |

Pemerataan beban: A dan D relatif ringan di minggu 1, jadi A mereview auth B, dan D membantu C menyiapkan data dummy dan skenario uji negatif.

## 6. Kontrak antarmuka (disepakati di hari 0)

1. **Modul kripto:** fungsi di `kcrypto/api.py` (sudah ada tanda tangannya). B memakainya tanpa tahu detail algoritma.
2. **Format file terenkripsi:** satu header seragam untuk ketiga algoritma. Spesifikasi ditulis A di `docs/04-desain-kripto.md`.
3. **API HTTP:** `openapi.yaml`. B menulis, C memakainya.
4. **Skema DB:** daftar tabel di `backend/README.md`.

Ubah kontrak hanya lewat Pull Request yang disetujui pemilik modul **dan** pemakainya.

## 7. Definition of Done (checklist akhir)

- [ ] Keempat jenis data dapat disimpan dan diambil kembali lewat UI
- [ ] Setiap item punya 3 salinan (AES, DES, RC4); plaintext hasil dekripsi ketiganya identik
- [ ] Tidak ada ECB; mode tiap cipher dijelaskan beserta alasannya
- [ ] User lain tidak bisa mengakses item (diuji). File yang diubah di storage terdeteksi (diuji)
- [ ] Tabel klasifikasi data memuat pasal yang sudah dicek ke teks resmi UU PDP dan GDPR
- [ ] Benchmark: spesifikasi mesin, metode, statistik (bukan hanya rata-rata), grafik, **interpretasi**
- [ ] Kesimpulan jujur tentang kelemahan DES dan RC4 dan rekomendasi untuk produksi
- [ ] `docker compose up` menjalankan seluruh sistem
- [ ] Laporan dan slide selesai; semua anggota bisa menjelaskan seluruh sistem

## 8. Cara menjalankan

_TODO (C): isi setelah `docker-compose.yml` berfungsi._
