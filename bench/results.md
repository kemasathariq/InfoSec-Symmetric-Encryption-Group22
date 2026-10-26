# Benchmark results

Environment: Python 3.14.3, Darwin arm64, arm, pycryptodome. Runs: 30 (+3 warm-up). Time = median [IQR] in ms.

## Time per object (random content)

| Object | Cipher | Encrypt ms | Decrypt ms | MB/s (enc) | MB/s (dec) | Overhead B | Peak mem (x size) |
|---|---|---|---|---|---|---|---|
| profile_1KB | AES | 0.09 [0.01] | 0.05 [0.00] | 11 | 19 | 47 | 29.3 |
| profile_1KB | DES | 0.08 [0.00] | 0.06 [0.00] | 13 | 17 | 55 | 16.8 |
| profile_1KB | RC4 | 0.06 [0.00] | 0.04 [0.00] | 17 | 27 | 51 | 26.7 |
| profile_1KB | AES+DES+RC4 | 0.20 [0.01] | 0.15 [0.01] | 5 | 7 | 156 | 46.1 |
| ktp_500KB | AES | 1.87 [0.08] | 1.85 [0.06] | 268 | 271 | 47 | 3.0 |
| ktp_500KB | DES | 10.81 [0.27] | 10.74 [0.26] | 46 | 47 | 55 | 3.0 |
| ktp_500KB | RC4 | 0.60 [0.03] | 0.54 [0.01] | 834 | 918 | 51 | 3.0 |
| ktp_500KB | AES+DES+RC4 | 13.33 [0.36] | 13.15 [0.24] | 38 | 38 | 156 | 4.1 |
| office_doc_2MB | AES | 7.34 [0.15] | 7.28 [0.17] | 273 | 275 | 47 | 3.0 |
| office_doc_2MB | DES | 43.86 [0.84] | 43.73 [0.67] | 46 | 46 | 55 | 3.0 |
| office_doc_2MB | RC4 | 2.24 [0.04] | 2.15 [0.04] | 892 | 931 | 51 | 3.0 |
| office_doc_2MB | AES+DES+RC4 | 53.57 [1.13] | 53.36 [0.75] | 37 | 37 | 156 | 4.0 |
| selfie_video_20MB | AES | 73.78 [0.66] | 73.21 [0.54] | 271 | 273 | 47 | 3.0 |
| selfie_video_20MB | DES | 448.13 [2.82] | 448.37 [3.12] | 45 | 45 | 55 | 3.0 |
| selfie_video_20MB | RC4 | 22.17 [0.25] | 21.60 [0.27] | 902 | 926 | 51 | 3.0 |
| selfie_video_20MB | AES+DES+RC4 | 546.09 [8.13] | 543.53 [3.27] | 37 | 37 | 156 | 4.0 |

## One registration (profile + KTP + doc + video), random content

| Cipher | Total encrypt ms | Total decrypt ms | vs AES (enc) |
|---|---|---|---|
| AES | 83 | 82 | 1.00x |
| DES | 503 | 503 | 6.05x |
| RC4 | 25 | 24 | 0.30x |
| AES+DES+RC4 | 613 | 610 | 7.38x |

## Side by side: one registration (profile + KTP + doc + video), random content

| Setup | Encrypt ms | Decrypt ms | vs all-AES | Extra bytes | Weakest protection of any item |
|---|---|---|---|---|---|
| All AES | 83 | 82 | 1.0x | 188 | AES |
| One cipher per data type (default) | 87 | 86 | 1.0x | 200 | DES (the KTP) |
| Layered AES+DES+RC4 on everything | 613 | 610 | 7.4x | 624 | all three, attacker must break each layer |

## Random vs repetitive content (selfie_video_20MB, encrypt, median ms)

| Cipher | Random | Repetitive | Difference |
|---|---|---|---|
| AES | 73.8 | 74.2 | 0.5% |
| DES | 448.1 | 450.9 | 0.6% |
| RC4 | 22.2 | 22.3 | 0.7% |
| AES+DES+RC4 | 546.1 | 547.7 | 0.3% |

HKDF key derivation per object: median 19 us, independent of size.

## RC4 keystream bias (2nd byte = 0, multiple of the ideal 1/256)

- No drop: 2.08x (ideal 1.00x, theory ~2x)
- Drop 3072: 1.00x
