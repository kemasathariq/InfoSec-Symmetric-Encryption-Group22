# frontend: antarmuka pasien + integrasi (Anggota C)

**Tugas:** C1-C10 di `TASKS.md`. **Status: hanya kerangka.** Framework final ditentukan di hari 0 (usulan: React + Vite).

## Yang harus dihasilkan
- [ ] Wireframe dan alur pasien (C1)
- [ ] Halaman: registrasi, login, data pribadi, unggah KTP, unggah dokumen, unggah video, dashboard "data saya" (C2-C5)
- [ ] Pemutar video untuk video yang didekripsi di server (C6)
- [ ] `docker-compose.yml` yang menjalankan seluruh sistem (C7)
- [ ] Data dummy + video demo di `scripts/` (C8)
- [ ] Tes end-to-end termasuk uji negatif (C9)

## Halaman dan fungsinya
| Halaman | Isi |
|---|---|
| Registrasi / Login | pesan error tidak membocorkan apakah email terdaftar |
| Data pribadi | form nama, NIK, tanggal lahir, alamat, riwayat penyakit, alergi |
| Unggah | KTP/BPJS (gambar), dokumen (docx/pdf/xlsx), video; progres; batas ukuran |
| Data saya | daftar item, unduh dengan **pilihan algoritma** (AES/DES/RC4), tombol **verifikasi 3 salinan**, hapus |
| Log akses | tampilan `GET /audit` |

## Urutan kerja yang disarankan
1. Mulai dari `openapi.yaml`: buat mock server atau data tiruan, jangan menunggu B.
2. Setelah B5 selesai, sambungkan ke API sungguhan.
3. Tulis tes E2E: unggah > keluar > login > unduh > bandingkan hash. Lalu uji negatif (akun lain, token kedaluwarsa, file diubah di storage).

## Catatan
- Jangan menyimpan token / kunci di tempat yang mudah dicuri (pertimbangkan cookie HttpOnly), dan tuliskan alasan pilihanmu di laporan.
- Unggah file besar: tampilkan progres dan tangani kegagalan di tengah jalan.
