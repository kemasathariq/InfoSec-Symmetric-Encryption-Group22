# Desain Kripto

_Pemilik: A._ Dikunci di hari 0 sebagai kontrak (B dan D bergantung padanya).

## 1. Pemilihan mode operasi
| Cipher | Mode / konstruksi | Alasan | Integritas | Risiko yang tersisa |
|---|---|---|---|---|
| AES | _TODO_ | | | |
| DES | _TODO_ | | | |
| RC4 | _TODO_ | | | |

Pertanyaan yang perlu dijawab A: mengapa ECB tidak dapat diterima? Bagaimana IV/nonce dikelola agar tidak berulang?
Mengapa RC4 tidak boleh memakai kunci yang sama dua kali?

## 2. Hierarki kunci
_TODO: diagram dan penjelasan: password -> KEK -> kunci pengguna -> kunci per item -> subkey per algoritma. Apa yang terjadi saat password diganti? Saat password hilang?_

## 3. Format file terenkripsi
_TODO: tabel field header (magic, versi, id algoritma, ukuran chunk, ukuran asli, salt, nonce, ...) dengan panjang byte.
Format harus **sama** untuk ketiga algoritma. Jelaskan apa yang diautentikasi dan bagaimana
penataan ulang / pemotongan chunk terdeteksi._

## 4. Penanganan file besar (video)
_TODO: ukuran chunk, bagaimana nonce/IV per chunk dibuat, batas ukuran file per kunci._

## 5. Ancaman yang ditangani dan yang tidak
_TODO_
