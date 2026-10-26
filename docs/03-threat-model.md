# Threat Model

_Pemilik: D, dengan masukan B dan A._

## Aset
_TODO: data pasien, kunci, kredensial, audit log, ..._

## Aktor ancaman
_TODO: pengguna lain yang login, penyerang eksternal, admin/orang dalam, pencuri disk/backup, ..._

## Ancaman dan kontrol

| # | Ancaman | Aset | Aktor | Kontrol | Diuji oleh |
|---|---|---|---|---|---|
| T1 | User lain mengakses item (IDOR) | | | | _TODO_ |
| T2 | Blob diubah di storage | | | | |
| T3 | Chunk diacak urutannya / dipotong | | | | |
| T4 | DB dan storage bocor | | | | |
| T5 | Brute force login | | | | |
| T6 | Penghapusan jejak akses | | | | |
| T7 | Pemakaian ulang keystream RC4 | | | | |
| T8 | _TODO tambahan_ | | | | |

## Risiko yang diterima (dan alasannya)
_TODO: misalnya DES dan RC4 dipakai hanya karena diwajibkan tugas._
