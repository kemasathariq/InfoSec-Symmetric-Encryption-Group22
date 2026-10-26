# Benchmark results

Environment: Python 3.14.3, Darwin arm64, arm, pycryptodome. Runs: 30 (+3 warm-up). Time = median [IQR] in ms.

## Time per object (random content)

| Object | Cipher | Encrypt ms | Decrypt ms | MB/s (enc) | MB/s (dec) | Overhead B | Peak mem (x size) |
|---|---|---|---|---|---|---|---|
| profile_1KB | AES | 0.09 [0.01] | 0.06 [0.00] | 11 | 18 | 47 | 29.4 |
| profile_1KB | DES | 0.08 [0.01] | 0.06 [0.00] | 13 | 17 | 55 | 16.8 |
| profile_1KB | RC4 | 0.06 [0.00] | 0.04 [0.00] | 16 | 26 | 51 | 26.7 |
| ktp_500KB | AES | 1.86 [0.09] | 1.84 [0.06] | 268 | 271 | 47 | 3.0 |
| ktp_500KB | DES | 10.74 [0.27] | 10.66 [0.26] | 47 | 47 | 55 | 3.0 |
| ktp_500KB | RC4 | 0.59 [0.02] | 0.55 [0.02] | 844 | 913 | 51 | 3.0 |
| office_doc_2MB | AES | 7.33 [0.20] | 7.23 [0.16] | 273 | 277 | 47 | 3.0 |
| office_doc_2MB | DES | 43.52 [0.91] | 43.52 [0.64] | 46 | 46 | 55 | 3.0 |
| office_doc_2MB | RC4 | 2.23 [0.06] | 2.13 [0.04] | 896 | 940 | 51 | 3.0 |
| selfie_video_20MB | AES | 73.64 [0.56] | 73.12 [0.57] | 272 | 274 | 47 | 3.0 |
| selfie_video_20MB | DES | 448.67 [3.78] | 448.39 [4.78] | 45 | 45 | 55 | 3.0 |
| selfie_video_20MB | RC4 | 22.07 [0.27] | 21.45 [0.27] | 906 | 933 | 51 | 3.0 |

## One registration (profile + KTP + doc + video), random content

| Cipher | Total encrypt ms | Total decrypt ms | vs AES (enc) |
|---|---|---|---|
| AES | 83 | 82 | 1.00x |
| DES | 503 | 503 | 6.07x |
| RC4 | 25 | 24 | 0.30x |

## Random vs repetitive content (selfie_video_20MB, encrypt, median ms)

| Cipher | Random | Repetitive | Difference |
|---|---|---|---|
| AES | 73.6 | 74.1 | 0.6% |
| DES | 448.7 | 451.2 | 0.6% |
| RC4 | 22.1 | 22.1 | 0.1% |

HKDF key derivation per object: median 19 us, independent of size.

## RC4 keystream bias (2nd byte = 0, multiple of the ideal 1/256)

- No drop: 1.94x (ideal 1.00x, theory ~2x)
- Drop 3072: 1.01x
