# bench: evaluasi perbandingan AES / DES / RC4 (Anggota D)

**Tugas:** D3-D8 di `TASKS.md`. **Status: hanya kerangka.**
Mulailah dari `docs/05-benchmark-plan.md`: **tulis rencananya dulu, baru kodenya.**

## Yang harus dihasilkan
- [ ] `docs/05-benchmark-plan.md` terisi (D3), termasuk hipotesis sebelum mengukur
- [ ] `variants.py`: varian yang diuji (D4)
- [ ] `harness.py`: pengukur yang andal (D4)
- [ ] `analyze.py`: statistik dan grafik (D7)
- [ ] Hasil mentah dan ringkasan di `results/` + spesifikasi mesin (D6)
- [ ] Interpretasi tertulis di laporan, bab 7 (D8)

## Pertanyaan desain yang harus kamu jawab sendiri
1. **Apa yang diukur?** Waktu, throughput, CPU, memori, overhead ukuran, biaya integritas, biaya 3 salinan. Mana yang relevan untuk skenario klinik?
2. **Bagaimana agar adil?** Cipher murni vs paket lengkap dengan integritas. Mode yang sama (mis. CTR vs CTR). Apa saja yang mengotori pengukuran?
3. **Bagaimana agar andal?** Warm-up, jumlah pengulangan, statistik selain rata-rata, isolasi proses, urutan acak, kondisi mesin, pemisahan dari disk dan jaringan.
4. **Berapa ukuran data uji?** Satu kelas per jenis data di skenario (teks kecil, scan KTP, dokumen, video).
5. **Apa artinya angka itu?** Hubungkan dengan AES-NI, ukuran kunci/blok, bias RC4, dan biaya HMAC. Jangan menyajikan angka tanpa penjelasan.

## Bergantung pada
Modul kripto A6. Sebelum selesai, kamu bisa menguji harness dengan fungsi cipher langsung dari PyCryptodome.

## Catatan
- Catat CPU, OS, versi Python/library, dan status AES-NI.
- Tulis hipotesis **sebelum** menjalankan; bila hasil tidak sesuai, laporkan apa adanya dan jelaskan.
- Hasil di `results/` tidak di-commit (lihat `.gitignore`); simpan ringkasan penting di laporan.
