# Rencana Benchmark

_Pemilik: D, dengan masukan A._ Ditulis **sebelum** menjalankan pengukuran.

## 1. Pertanyaan yang ingin dijawab
_TODO: contoh: Cipher mana yang paling praktis untuk tiap kelas data di skenario kami? Berapa biaya menyimpan 3 salinan? Berapa biaya integritas?_

## 2. Apa yang diukur
| Metrik | Satuan | Cara ukur | Mengapa penting untuk skenario |
|---|---|---|---|
| Waktu enkripsi / dekripsi | ms | _TODO_ | |
| Throughput | MiB/s | | |
| CPU time | ms | | |
| Memori puncak | KiB | | |
| Overhead ukuran | byte, % | | |
| Biaya integritas | % | | |
| Biaya 3 salinan | × | | |

## 3. Kelas data uji
| Kelas | Ukuran | Alasan |
|---|---|---|
| Profil (teks) | _TODO_ | |
| Scan KTP | | |
| Dokumen kantor | | |
| Video | | |

## 4. Agar pengukuran dapat dipercaya
_TODO: jumlah warm-up, jumlah pengulangan, statistik yang dilaporkan, isolasi proses, urutan acak, pemisahan I/O, perbandingan adil antar mode, spesifikasi mesin (termasuk AES-NI), kondisi mesin saat uji._

## 5. Hipotesis (tulis sebelum mengukur)
_TODO: prediksi urutan kecepatan dan alasannya._

## 6. Ancaman terhadap validitas
_TODO: apa yang dapat membuat hasil menyesatkan?_
