https://claude.ai/share/25e42851-47ed-4a73-b657-b69a2160df18
Listed directory lab-session-information-security-main
Viewed README.md:1-155
Viewed crypto_tool.py:1-194
Listed directory Simple-Mobile-Banking
Viewed PRD%20%E2%80%93%20Mobile%20Banking%20dengan%20Perlindungan%20Data%20Simetris.md:1-100
Viewed PRD%20%E2%80%93%20Mobile%20Banking%20dengan%20Perlindungan%20Data%20Simetris.md:101-210
Viewed hooks.py:1-20
Viewed App.py:1-60
Searched for "hooks"
Viewed App.py:130-246

Berikut adalah penjelasan komprehensif mengenai **arsitektur dan alur implementasi enkripsi** untuk tugas ini, dengan mengacu langsung pada implementasi di [`crypto_tool.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/lab-session-information-security-main/crypto_tool.py) serta kaitannya dengan aplikasi web perbankan Anda di [`Simple-Mobile-Banking`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking).

---

### 1. Mengapa Skenario Mobile Banking (e-KYC) Sangat Tepat untuk Soal Ini?

Soal tugas meminta skenario nyata dengan 4 jenis data:
1. **Personal Data:** Data diri nasabah (Nama, NIK, alamat, tanggal lahir, dsb.) $\rightarrow$ di aplikasi Anda berupa *JSON profile blob*.
2. **Scanned Identity Document:** Scan KTP $\rightarrow$ file gambar/PDF (`ktp`).
3. **Office Documents:** Bukti penghasilan / slip gaji $\rightarrow$ file dokumen (`supporting_doc`).
4. **Video:** Video selfie untuk verifikasi biometrik $\rightarrow$ file multimedia (`selfie_video`).

Berdasarkan **UU PDP No. 27/2022** dan **GDPR**, data keuangan dan biometrik adalah **Data Pribadi Spesifik** (*sensitive personal data*). Jika database atau hard disk server bocor, penyerang tidak boleh bisa membaca file-file ini.

---

### 2. Bedah Logika Kriptografi dari [`crypto_tool.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/lab-session-information-security-main/crypto_tool.py)

Di dalam file lab session [`crypto_tool.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/lab-session-information-security-main/crypto_tool.py), sudah tersedia fungsi-fungsi inti menggunakan library `pycryptodome` yang memenuhi seluruh syarat teknis tugas:

#### A. Mode Operasi & Padding (Tidak Menggunakan ECB)
Soal menegaskan: *"ECB is not acceptable"*. Di `crypto_tool.py`:
- **AES:** Menggunakan **AES-CBC** (`AES.MODE_CBC`), membutuhkan IV berukuran 16 byte (`AES_IV_SIZE = 16`).
- **DES:** Menggunakan **DES-CBC** (`DES.MODE_CBC`), membutuhkan IV berukuran 8 byte (`DES_IV_SIZE = 8`).
- **RC4:** Merupakan **Stream Cipher** (enkripsi byte-per-byte langsung dengan keystream), sehingga **tidak memakai mode block dan tidak butuh IV/padding**.
- **Padding:** Algoritma block cipher (AES & DES) menggunakan fungsi `pkcs7pad` dan `pkcs7unpad` pada baris 40–51 agar panjang byte data pas kelipatan ukuran blok cipher (16 byte untuk AES, 8 byte untuk DES).

#### B. Key Derivation Function (KDF)
Di baris 34–37:
```python
def derive(password: str, salt: bytes, length: int) -> bytes:
    return PBKDF2(password, salt, dkLen=length, count=PBKDF2_ROUNDS, hmac_hash_module=SHA256)
```
- Menghasilkan kunci simetris dengan panjang yang sesuai:
  - AES: 32 byte (256 bit)
  - DES: 8 byte (64 bit, efektif 56 bit)
  - RC4: 32 byte (256 bit)
- Menggunakan `salt` acak 16 byte (`secrets.token_bytes(16)`) sehingga ciphertext berbeda meskipun password atau plaintext sama.

#### C. Format Penyimpanan (Envelope)
Di baris 59–80 dan 83–109:
Setiap enkripsi menghasilkan envelope (data pembungkus) yang memuat metadata penting:
- Algoritma (`algorithm`)
- Salt acak (`salt`)
- IV acak (`iv`) — khusus AES dan DES
- Ciphertext (`ciphertext`)

---

### 3. Cara Mengintegrasikannya ke Web App (`Simple-Mobile-Banking`)

Di project `Simple-Mobile-Banking`, arsitektur backend Anda sudah dirancang sangat elegan: **semua data privat terpusat di satu titik**: [`hooks.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/hooks.py).

#### A. Di Mana Letak Enkripsi & Dekripsi?
Jika kita lihat di [`App.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/App.py):
1. **Saat Pendaftaran (`/api/register`):**
   - Profil JSON dienkripsi sebelum masuk database:
     ```python
     hooks.protect(profile, user_id=uid, purpose="profile")
     ```
   - Ketiga file (KTP, Dokumen, Video) dienkripsi sebelum ditulis ke disk `storage/<user_id>/`:
     ```python
     path.write_bytes(hooks.protect(data, user_id=uid, purpose=kind))
     ```
2. **Saat Data Diambil (`/api/me` dan `/api/me/documents/<kind>`):**
   - Dibaca dari database / disk, lalu didekripsi kembali:
     ```python
     hooks.unprotect(...)
     ```

Artinya, **Anda tidak perlu merombak rute di `App.py`**. Kita cukup mengisi implementasi fungsi `protect()` dan `unprotect()` di [`hooks.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/hooks.py).

#### B. Perbedaan Penting: Password vs. Server Key
- Di `crypto_tool.py` (CLI), user mengetik password setiap kali ingin enkripsi/dekripsi.
- Di aplikasi web backend, enkripsi data-at-rest (database & storage) biasanya menggunakan **Server Master Key** (disimpan di environment variable, misal `APP_SECRET_KEY`) yang dikombinasikan dengan KDF (`salt` acak + `user_id` / `purpose`) untuk menurunkan kunci enkripsi spesifik per objek.
- Dengan cara ini:
  - Sistem tidak bergantung pada plaintext password nasabah saat server perlu membaca kembali dokumen.
  - Setiap nasabah dan setiap file memiliki kunci turunan dan IV/salt yang berbeda-beda.

#### C. Pilihan Format Simpan Ciphertext di Disk
Ada dua opsi format penyimpanan hasil enkripsi ke file `.bin` di `storage/`:
1. **Opsi 1: Format JSON Envelope (Persis seperti `crypto_tool.py`)**
   - Menghasilkan string JSON yang di-*encode* ke bytes (memuat base64 dari salt, iv, ciphertext).
   - *Kelebihan:* Sangat mudah dibaca, diinspeksi, dan 100% identik dengan modul lab session Anda.
2. **Opsi 2: Format Binary Prefix (Header Biner)**
   - Header biner ringkas: `[salt: 16 bytes] + [iv: 8/16 bytes] + [raw ciphertext]`.
   - *Kelebihan:* Tidak terkena overhead base64 (~33% lebih besar), sehingga sangat efisien terutama untuk video berukuran 20–50 MB.

*(Kedua opsi ini valid; Opsi 1 paling mudah dihubungkan langsung dengan kode `crypto_tool.py`).*

---

### 4. Menjawab Semua Poin Kriteria Penilaian

| Syarat di Soal Tugas | Solusi Implementasi di Aplikasi Kita |
| :--- | :--- |
| **Skenario spesifik nyata** | *Digital Banking Onboarding (e-KYC)* untuk pembukaan rekening tabungan online. |
| **4 Jenis data (Personal, KTP, Office, Video)** | `profile` (JSON), `ktp` (image/pdf), `supporting_doc` (office doc), `selfie_video` (video biometrik). |
| **Alasan UU PDP / GDPR** | Diklasifikasikan di PRD: NIK/nama adalah data pribadi umum; video selfie (biometrik) & slip gaji (finansial) adalah data pribadi spesifik. |
| **3 Cipher: AES, DES, RC4** | `CURRENT_CIPHER` di `hooks.py` yang dapat diganti (`aes`, `des`, `rc4`) dan kolom `cipher` di DB mencatat cipher yang dipakai. |
| **Non-ECB Mode** | AES & DES memakai mode **CBC** dengan random IV per enkripsi. RC4 memakai stream keystream acak per enkripsi. |
| **Hanya user terautentikasi** | Rute `/api/me` dilindungi token Bearer (session) dan query database selalu memfilter `WHERE user_id = g.user_id`. |
| **Data kembali utuh** | Di `App.py` baris 239, terdapat verifikasi hash: jika `sha256(decrypted_data) != original_sha256`, request dibatalkan/error. Ini membuktikan data kembali utuh 100%. |
| **Evaluasi komparatif** | Membuat skrip benchmark terpisah untuk mengukur: waktu enkripsi/dekripsi, throughput (MB/s), dan perbedaan ukuran file untuk ketiga cipher. |

---

### 5. Rencana Tahapan Eksekusi Selanjutnya

Jika Anda sudah sepakat dengan alur ini, berikut langkah konkret yang akan kita lakukan:
1. **Tahap 1:** Membawa fungsi inti dari `crypto_tool.py` (KDF, CBC encryption, padding, RC4) ke dalam modul crypto di folder `Simple-Mobile-Banking` (atau langsung di `hooks.py`).
2. **Tahap 2:** Melengkapi fungsi `protect()` dan `unprotect()` di [`hooks.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/hooks.py) agar mendukung `AES`, `DES`, dan `RC4`.
3. **Tahap 3:** Menjalankan uji pendaftaran (registrasi) dan unduh dokumen untuk membuktikan bahwa file terenkripsi di folder storage dan dapat diunduh kembali utuh (hash SHA-256 cocok).
4. **Tahap 4:** Menyiapkan skrip benchmark untuk mengumpulkan data perbandingan kinerja ketiga cipher untuk laporan.

Silakan sampaikan jika ada konsep atau bagian dari alur di atas yang ingin Anda sesuaikan sebelum kita melangkah ke pengeditan kode!

Jawabannya adalah **MEMILIH (bukan dienkripsi bertingkat/berlapis 3 sekaligus)**.

Berikut adalah penjelasan mengapa mekanismenya adalah memilih salah satu cipher, beserta bukti dari referensi tugas dan kodenya:

---

### 1. Mengapa Bukan Enkripsi Berlapis (Cascade / 3 Sekaligus)?

Kalimat pada soal:  
> *"Everything you store must be protected with each of the following ciphers: AES, DES, RC4. Evaluate how the three ciphers compare in practice."*

Maksud dari kalimat tersebut adalah: **aplikasi Anda harus mendukung dan mampu mengamankan data dengan masing-masing dari ketiga cipher tersebut**, sehingga Anda bisa **membandingkan kinerja dan karakteristik ketiganya**.

Jika data dienkripsi bertingkat (misal: Plaintext $\rightarrow$ AES $\rightarrow$ DES $\rightarrow$ RC4):
1. **Tidak bisa dievaluasi secara adil (*compare in practice*):** Anda tidak akan bisa mengukur berapa lama waktu murni enkripsi video jika hanya memakai AES saja, DES saja, atau RC4 saja.
2. **Kombinasi algoritma usang:** Menumpuk DES (kunci 56-bit yang rentan) dan RC4 di atas AES-256 tidak lazim dalam skenario perbankan dan justru menambah overhead tanpa manfaat keamanan.

---

### 2. Bukti dari File Referensi Lab ([`crypto_tool.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/lab-session-information-security-main/crypto_tool.py))

Jika kita lihat implementasi asli di [`crypto_tool.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/lab-session-information-security-main/crypto_tool.py#L54-L79):

```python
def encryptbytes(data: bytes, password: str, algorithm: str = "AES", name: str = "data") -> bytes:
    algorithm = algorithm.upper()
    ...
    if algorithm == "AES":
        # Enkripsi murni dengan AES-CBC
    elif algorithm == "DES":
        # Enkripsi murni dengan DES-CBC
    else:
        # Enkripsi murni dengan RC4
```

Di CLI-nya pun pengguna memilih dengan argumen `-a`:
- `python crypto_tool.py encrypt -i ktp.jpg -a AES`
- `python crypto_tool.py encrypt -i ktp.jpg -a DES`
- `python crypto_tool.py encrypt -i ktp.jpg -a RC4`

Setiap file dienkripsi oleh **satu algoritma yang dipilih**, lalu nama algoritma tersebut dicatat ke dalam metadata envelope JSON:
```json
{
    "algorithm": "AES",
    "salt": "...",
    "iv": "...",
    "ciphertext": "..."
}
```

---

### 3. Bagaimana Cara Kerjanya di Aplikasi Kita (`Simple-Mobile-Banking`)?

Di database yang sudah Anda buat ([`db.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/db.py) dan [`App.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/App.py)), arsitekturnya sudah disiapkan untuk sistem **pemilihan cipher**:

1. **Ada kolom `cipher` di database:**
   - Tabel `users` memiliki kolom `cipher` (mencatat apakah profil nasabah ini dienkripsi pakai AES, DES, atau RC4).
   - Tabel `documents` memiliki kolom `cipher` (mencatat algoritma file terkait).
2. **Saat Enkripsi (`hooks.protect`):**
   - Menggunakan cipher yang sedang aktif / dipilih (misalnya dikontrol oleh `CURRENT_CIPHER = "AES"` di [`hooks.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/hooks.py), atau opsi pilihan dropdown di form registrasi).
3. **Saat Dekripsi (`hooks.unprotect`):**
   - Fungsi dekripsi membaca metadata (dari kolom database atau dari envelope file). Jika tercatat `"DES"`, sistem otomatis mendekripsi menggunakan alur DES. Jika `"AES"`, menggunakan AES.
4. **Saat Evaluasi/Benchmark (Tahap Evaluasi):**
   - Kita membuat skrip uji yang menjalankan file yang sama (KTP 500 KB, Dokumen 2 MB, Video 30 MB) ke dalam AES, lalu DES, lalu RC4. Dari situ kita dapat tabel perbandingan:
     - Waktu enkripsi & dekripsi (ms)
     - Throughput (MB/s)
     - Ukuran file hasil enkripsi vs aslinya.

### Kesimpulan
**Kita memilih salah satu cipher per operasi/transaksi**. Sistem mampu mengenkripsi dan mendekripsi dengan **ketiga-tiganya**, sehingga data dari ketiga cipher tersebut bisa diuji, dibandingkan kinerjanya, dan disimpan/diambil kembali secara utuh.

Viewed App.py:123-152

Berikut adalah rancangan implementasi lengkap untuk [`hooks.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/hooks.py) yang diadaptasi langsung dari logika lab session [`crypto_tool.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/lab-session-information-security-main/crypto_tool.py). 

Kode ini siap Anda gunakan sebagai acuan:

```python
"""
hooks.py - Modul Enkripsi Data Simetris untuk Mobile Banking
Mengacu pada implementasi crypto_tool.py (AES-CBC, DES-CBC, RC4).

Fitur:
- AES-256-CBC (dengan random IV 16 bytes & PKCS#7 padding)
- DES-CBC (dengan random IV 8 bytes & PKCS#7 padding)
- RC4 (Stream cipher dengan keystream unik via salt KDF)
- Self-describing JSON envelope: menyimpan salt, iv, dan ciphertext dalam Base64.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
from typing import Any

from Crypto.Cipher import AES, ARC4, DES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import PBKDF2

# ================= KONFIGURASI =================
# Anda bisa mengubah CURRENT_CIPHER ini ke: "AES", "DES", "RC4", atau "none"
CURRENT_CIPHER = os.environ.get("APP_CIPHER", "AES").upper()

# Kunci master aplikasi (dalam praktik riil diambil dari environment variable)
MASTER_KEY = os.environ.get("APP_MASTER_KEY", "bank-digital-super-secret-master-key-2026")

SALT_SIZE = 16
AES_IV_SIZE = 16
DES_IV_SIZE = 8
# PBKDF2 iterations (rekomendasi lab: 600_000, atau sesuaikan untuk kecepatan benchmark)
PBKDF2_ROUNDS = int(os.environ.get("PBKDF2_ROUNDS", "100000"))
ALGORITHMS = {"AES", "DES", "RC4"}


# ================= HELPER BASE64 =================
def b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def unb64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


# ================= KEY DERIVATION (PBKDF2) =================
def derive_key(user_id: int, purpose: str, salt: bytes, length: int) -> bytes:
    """
    Menurunkan kunci enkripsi spesifik per user dan per tujuan data (purpose).
    Kombinasi MASTER_KEY + user_id + purpose memastikan setiap user dan
    setiap jenis dokumen memiliki kunci unik, meskipun salt sama.
    """
    context_secret = f"{MASTER_KEY}:{user_id}:{purpose}"
    return PBKDF2(context_secret, salt, dkLen=length, count=PBKDF2_ROUNDS, hmac_hash_module=SHA256)


# ================= PADDING PKCS#7 =================
def pkcs7pad(data: bytes, block_size: int) -> bytes:
    padding = block_size - len(data) % block_size
    return data + bytes([padding]) * padding


def pkcs7unpad(data: bytes, block_size: int) -> bytes:
    if not data or len(data) % block_size:
        raise ValueError("Invalid padding: panjang data tidak sesuai kelipatan blok.")
    padding = data[-1]
    if padding < 1 or padding > block_size or data[-padding:] != bytes([padding]) * padding:
        raise ValueError("Invalid padding: byte padding tidak valid.")
    return data[:-padding]


# ================= TITIK COLOKAN UTAMA: PROTECT =================
def protect(data: bytes, *, user_id: int, purpose: str) -> bytes:
    """
    Mengenkripsi data sebelum disimpan ke database (profil) atau disk (file).
    Mengembalikan data terenkripsi dalam format JSON envelope (bytes).
    """
    alg = CURRENT_CIPHER.upper()
    if alg == "NONE":
        return data

    if alg not in ALGORITHMS:
        raise ValueError(f"Algoritma '{alg}' tidak didukung. Pilih salah satu: AES, DES, RC4.")

    salt = secrets.token_bytes(SALT_SIZE)
    envelope: dict[str, Any] = {
        "algorithm": alg,
        "purpose": purpose,
        "salt": b64(salt),
    }

    if alg == "AES":
        key = derive_key(user_id, purpose, salt, length=32)  # AES-256
        iv = secrets.token_bytes(AES_IV_SIZE)
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        ciphertext = cipher.encrypt(pkcs7pad(data, AES.block_size))
        envelope.update(iv=b64(iv), ciphertext=b64(ciphertext))

    elif alg == "DES":
        key = derive_key(user_id, purpose, salt, length=8)   # DES 64-bit (56-bit efektif)
        iv = secrets.token_bytes(DES_IV_SIZE)
        cipher = DES.new(key, DES.MODE_CBC, iv=iv)
        ciphertext = cipher.encrypt(pkcs7pad(data, DES.block_size))
        envelope.update(iv=b64(iv), ciphertext=b64(ciphertext))

    elif alg == "RC4":
        key = derive_key(user_id, purpose, salt, length=32)  # RC4 256-bit
        cipher = ARC4.new(key)
        ciphertext = cipher.encrypt(data)  # Stream cipher tidak memerlukan padding
        envelope.update(ciphertext=b64(ciphertext))

    # Kembalikan JSON envelope dalam bentuk bytes
    return json.dumps(envelope).encode("utf-8")


# ================= TITIK COLOKAN UTAMA: UNPROTECT =================
def unprotect(data: bytes, *, user_id: int, purpose: str) -> bytes:
    """
    Mendekripsi data saat dibaca dari database atau disk.
    Membaca metadata algoritma langsung dari envelope, sehingga jika ada
    dokumen lama terenkripsi DES dan dokumen baru AES, keduanya tetap bisa didekripsi.
    """
    # Jika data bukan envelope JSON (misal data plain lama saat mode 'none')
    try:
        envelope = json.loads(data.decode("utf-8"))
        if not isinstance(envelope, dict) or "algorithm" not in envelope:
            return data
    except (UnicodeDecodeError, json.JSONDecodeError):
        return data

    alg = envelope["algorithm"].upper()
    if alg not in ALGORITHMS:
        raise ValueError(f"Algoritma envelope tidak dikenal: {alg}")

    salt = unb64(envelope["salt"])
    ciphertext = unb64(envelope["ciphertext"])

    if alg == "AES":
        key = derive_key(user_id, purpose, salt, length=32)
        iv = unb64(envelope["iv"])
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        return pkcs7unpad(cipher.decrypt(ciphertext), AES.block_size)

    elif alg == "DES":
        key = derive_key(user_id, purpose, salt, length=8)
        iv = unb64(envelope["iv"])
        cipher = DES.new(key, DES.MODE_CBC, iv=iv)
        return pkcs7unpad(cipher.decrypt(ciphertext), DES.block_size)

    elif alg == "RC4":
        key = derive_key(user_id, purpose, salt, length=32)
        cipher = ARC4.new(key)
        return cipher.decrypt(ciphertext)

    raise ValueError("Gagal mendekripsi: format tidak valid.")
```

---

### Penjelasan Mengapa Desain Ini Memenuhi Semua Syarat Tugas:

1. **Non-ECB Mode (Sesuai Technical Requirements):**
   - AES menggunakan `AES.MODE_CBC` dengan IV 16-byte acak.
   - DES menggunakan `DES.MODE_CBC` dengan IV 8-byte acak.
   - RC4 adalah stream cipher (tidak memakai block mode / tidak ada ECB).
2. **Kunci Dinamis per Pengguna (`user_id` & `purpose`):**
   - Menggunakan fungsi `derive_key()` berbasis PBKDF2-HMAC-SHA256. Setiap kali nasabah menyimpan KTP atau video, kunci yang dihasilkan unik berkat salt acak dan context (`user_id` + `purpose`).
3. **Format Envelope Self-Describing:**
   - Karena envelope menyimpan informasi `"algorithm"`, fungsi `unprotect()` **bisa mendeteksi otomatis** apakah data tersebut dienkripsi dengan AES, DES, atau RC4 tanpa perlu parameter tambahan.
4. **Menjamin "Data Kembali Utuh":**
   - Saat diunduh di [`App.py`](file:///C:/Users/Ramadhan%20Aditya/OneDrive/Documents/Insyaallah%20Tabarakallah%20Selalu/Semester%205/KI/Simple-Mobile-Banking/App.py#L238-L240):
     ```python
     data = hooks.unprotect(Path(row["path"]).read_bytes(), user_id=g.user_id, purpose=kind)
     if hashlib.sha256(data).hexdigest() != row["sha256"]:
         return err("Integritas file gagal diverifikasi", 500)
     ```
     Fungsi `unprotect` di atas mengembalikan byte asli yang persis sama, sehingga pengecekan `sha256` di `App.py` akan lolos dengan sempurna.

---

### Contoh Skrip Pengujian Singkat (Round-Trip Test)

Untuk membuktikan bahwa ketiga cipher bekerja dan data kembali 100% utuh sebelum disambungkan ke web/UI, Anda bisa membuat skrip uji sederhana seperti ini:

```python
import hashlib
import hooks

dummy_data = b"Ini adalah contoh dokumen scan KTP rahasia nasabah 1234567890."
original_hash = hashlib.sha256(dummy_data).hexdigest()

for alg in ["AES", "DES", "RC4"]:
    hooks.CURRENT_CIPHER = alg
    
    # 1. Enkripsi (protect)
    encrypted_blob = hooks.protect(dummy_data, user_id=1, purpose="ktp")
    
    # 2. Dekripsi (unprotect)
    decrypted_data = hooks.unprotect(encrypted_blob, user_id=1, purpose="ktp")
    decrypted_hash = hashlib.sha256(decrypted_data).hexdigest()
    
    # 3. Verifikasi
    assert dummy_data == decrypted_data, f"Data {alg} tidak cocok!"
    assert original_hash == decrypted_hash, f"Hash {alg} tidak cocok!"
    print(f"[{alg}] Sukses! Data kembali utuh (SHA-256 Valid). Ukuran: {len(dummy_data)}B -> {len(encrypted_blob)}B")
```

Apakah struktur acuan di atas sudah jelas dan sesuai dengan yang Anda harapkan? Jika sudah sesuai, kita bisa lanjutkan ke langkah berikutnya!
