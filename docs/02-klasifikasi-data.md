# Klasifikasi Data berdasarkan UU PDP dan GDPR

_Pemilik: D._ **Seluruh nomor pasal harus dicek langsung ke teks resmi, bukan dari artikel blog.**

## Sumber yang dipakai
- UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi: _TODO tautan teks resmi (JDIH / peraturan.go.id)_
- Regulation (EU) 2016/679 (GDPR): _TODO tautan EUR-Lex_

## Pertanyaan yang harus dijawab
1. Bagaimana kedua regulasi membagi data pribadi? Apa kriteria "spesifik" (UU PDP) dan "kategori khusus" (GDPR)?
2. Tiap jenis data di skenario masuk kategori mana, dan **mengapa**? (Beri argumen, bukan hanya label.)
3. Data mana yang tetap kami simpan sebagai plaintext (misalnya identitas login), dan mengapa itu dapat dipertanggungjawabkan?
4. Kewajiban keamanan apa yang disebut regulasi, dan kontrol mana di sistem kami yang memenuhinya?

## Tabel klasifikasi

| Data | Contoh | Pasal UU PDP | Pasal GDPR | Tingkat | Perlakuan di sistem | Argumen |
|---|---|---|---|---|---|---|
| Riwayat penyakit, alergi, hasil lab | | _TODO_ | _TODO_ | | | |
| Video konsultasi | | _TODO_ | _TODO_ | | | |
| Scan KTP / BPJS | | _TODO_ | _TODO_ | | | |
| NIK, nama, tgl lahir, alamat | | _TODO_ | _TODO_ | | | |
| Data pasien anak | | _TODO_ | _TODO_ | | | |
| Email login | | _TODO_ | _TODO_ | | | |
| Nama file asli (bisa membocorkan isi) | | _TODO_ | _TODO_ | | | |
| Audit log (user id, IP) | | _TODO_ | _TODO_ | | | |
| Hash password, kunci terbungkus | | - | - | rahasia sistem | | |

## Kewajiban keamanan dan kontrol yang memenuhinya

| Kewajiban (pasal) | Kontrol di sistem | Bukti |
|---|---|---|
| _TODO: keamanan pemrosesan_ | | |
| _TODO: pencatatan kegiatan pemrosesan_ | | |
| _TODO: notifikasi kegagalan pelindungan data_ | | |
| _TODO: hak penghapusan data_ | | |
