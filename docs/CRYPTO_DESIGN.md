# Crypto Design and Evaluation

Code: `BE/ciphers.py`, `BE/Hooks.py`, `tests/`, `bench/`.
Reference book: Stallings, Cryptography and Network Security, 7th ed. Page numbers are the printed book pages (the PDF can be off by one).

Short terms used here:
- **Nonce / IV**: a random value used once per encryption, so the same data never encrypts the same way twice.
- **MAC / tag**: a short code that proves the data was not changed. We use the GCM tag or HMAC-SHA256.
- **Key per object**: every stored item gets its own key.

## 1. What each cipher does

| | AES | DES | RC4 |
|---|---|---|---|
| Setup | AES-256 in GCM mode | DES in CTR mode + HMAC-SHA256 | RC4 + HMAC-SHA256, first 3072 bytes skipped |
| Nonce / IV | 12 random bytes | 4 random bytes + 4-byte counter | none |
| Integrity check | GCM tag (16 bytes) | HMAC (32 bytes) | HMAC (32 bytes) |
| Extra size per item | 47 bytes | 55 bytes | 51 bytes |
| Used for | profile, selfie video | KTP scan | office document |

All three ciphers run at the same time. By default each data type uses one of them (section 4). There is also a layered setup where every item uses all three (section 4b). Every stored item remembers which cipher it used, so the setting can change later without breaking old data.

Stored item: `magic | cipher_id | salt | iv/nonce | ciphertext | tag`

## 2. Keys

- `MASTER_KEY` comes from an environment variable. Make it random: `python -c "import secrets; print(secrets.token_hex(32))"`.
- Each item gets its own key from the master key, a random salt, the cipher name, `user_id` and the data type (HKDF-SHA256). This takes about 19 microseconds.
- The tag also checks `user_id` and the data type. If a stored item is copied to another user, decryption fails.

Why one key per item:
- A key and nonce pair is never used twice. Reusing one is a serious mistake for GCM, CTR and RC4.
- If one key leaks, only that item is exposed.
- It gives RC4 something to make each output unique, since RC4 has no IV.

Known limits:
- `MASTER_KEY` is on the same server as the data. If the server is hacked, the key is too. A key management service would fix this. It is outside this project.
- Items do not store a key version. Changing the master key means re-encrypting everything.

## 3. Why these modes

Rule: pick the fastest mode that is equally safe. If a ready-made mode with built-in integrity exists (GCM), use it, so we do not have to combine encryption and HMAC ourselves.

Measured on a 20 MB file, median of 30 runs (`bench/mode_comparison.py`):

| Variant | Time (ms) | MB/s |
|---|---|---|
| AES-CTR + HMAC | 62.2 | 321 |
| AES-CBC + HMAC | 71.6 | 279 |
| **AES-GCM** | **72.7** | **275** |
| **DES-CTR + HMAC** | **447** | **45** |
| DES-OFB + HMAC | 512 | 39 |
| DES-CBC + HMAC | 521 | 38 |

- **AES-GCM.** GCM is CTR mode plus a built-in tag (Stallings 12.7, p. 402-408). It encrypts and checks integrity in one step. CTR + HMAC is 14% faster, about 10 ms on 20 MB, which nobody notices. XTS-AES (Stallings 7.7) is not used because it is made for disk sectors and has no integrity check.
- **DES-CTR + HMAC.** DES has no built-in integrity mode, so we add HMAC. CTR is the fastest DES mode and needs no padding (Stallings 7.6, p. 224). DES has a limit of about 32 GB per key, which does not matter because each item has its own key and uploads are capped at 60 MB.
- **RC4.** It has no modes. We skip the first 3072 output bytes because they are biased. We add HMAC because RC4 has no integrity check.
- **No ECB anywhere.** ECB encrypts identical blocks to identical ciphertext (Stallings 7.2, p. 213), so it is not used in the app, the tests or the benchmark.
- For DES and RC4 the HMAC is checked before decrypting.

### Why not CBC

The lab reference uses CBC. CBC is not broken, and CBC with HMAC is safe. We did not use it because:
1. CBC has no integrity check. Flipping a bit in one block garbles that block and flips the same bit in the next one, and nothing notices. We would need HMAC anyway.
2. CBC needs padding, which is extra code and can leak information through error messages. CTR and GCM need no padding.
3. CBC encrypts one block at a time in order, because each block depends on the one before (Stallings 7.3). CTR and GCM can run in parallel (Stallings 7.6).
4. No speed gain. AES-CBC + HMAC took 71.6 ms and GCM took 72.7 ms, a tie. DES-CBC took 521 ms and DES-CTR took 447 ms.

So CBC is as fast as GCM for AES, slower for DES, and needs more code to be safe.

## 4. Which cipher for which data

The assignment needs all three ciphers, and we want to compare them and choose per data type. Rule: the worse a leak would be, the stronger the cipher. From the results in section 6, the order is AES-GCM, then RC4, then DES. RC4 has a 128-bit key with no shortcut to find it, but its output is slightly biased. DES has a 56-bit key that can be brute-forced.

| Data | Size | Cipher | Reason |
|---|---|---|---|
| Profile (NIK, name, birth date, address, email, phone) | 1 KB | AES-GCM | Most identity data per byte. It is tiny, so speed does not matter. |
| Selfie video | up to 60 MB | AES-GCM | Biometric data that cannot be replaced (GDPR Art. 9). It is also the biggest file, where DES is slowest (0.45 s per 20 MB). |
| Office document (payslip) | about 2 MB | RC4 + HMAC | Financial data, medium harm. RC4 is fast (2 ms) and each item has its own key. |
| KTP scan | about 500 KB | DES-CTR + HMAC | Least harm in the set: the same fields are also in the encrypted profile, and KTP copies are shared widely. It is small, so DES takes only 11 ms. |

Cost of this setup for one registration: 87 ms (all AES: 83 ms).

Limits to write in the report:
- We use DES and RC4 only because the assignment requires all three. DES only stops casual access. Its 56-bit key can be searched (Stallings Table 4.5), and a known file header such as JPEG makes it easy to check a guess.
- For real use, switch everything to AES with `CIPHER=aes`.
- Change single entries with `CIPHER_POLICY=ktp=aes,supporting_doc=aes`. Old items still decrypt.

### 4b. Layered option, side by side

Our TA said the assignment can be read two ways, so the app supports both and we compare them. Switch with one setting:

| Setup | Setting | What it does |
|---|---|---|
| One cipher per data type | none (default) | The table above |
| Layered | `CIPHER=layered` | Every item is encrypted with AES-GCM, that result with DES-CTR + HMAC, and that result with RC4 + HMAC |
| All AES | `CIPHER=aes` | One cipher for everything, for comparison and real use |

How layered works: each layer has its own key (derived with a different label) and its own tag. The label of each layer also contains its position and the total number of layers. So removing a layer, adding one, or changing the count is detected (tested).

Results for one registration (profile + KTP + payslip + video), random data, median of 30 runs (`bench/results.md`):

| Setup | Encrypt | Decrypt | vs all-AES | Extra bytes | Weakest protection of any item |
|---|---|---|---|---|---|
| All AES | 83 ms | 82 ms | 1.0x | 188 | AES |
| One cipher per data type | 87 ms | 86 ms | 1.0x | 200 | DES (the KTP) |
| Layered AES + DES + RC4 | 613 ms | 610 ms | 7.4x | 624 | an attacker must break all three layers |

For the 20 MB video alone: AES 74 ms, layered 546 ms.

What it shows:
1. **Cost.** Layered is 7.4x slower, but still small next to a 16 s upload. For 100 signups at once it is about 61 CPU-seconds against 8.7 (per type) and 8.3 (all AES). Memory peaks at about 4x the file size instead of 3x.
2. **Size.** Layered adds 156 bytes per item. It does not matter.
3. **Protection.** In the per-type setup the KTP is protected only by DES and the payslip only by RC4. In the layered setup every item has AES inside, so no item is weaker than AES. In general, layers with independent keys are at least as hard to break as the strongest layer. We did not test this, it is a general result.
4. **The extra layers add little.** If AES holds, the DES and RC4 layers add nothing. If AES were ever broken, they would still help, but DES can be brute-forced and RC4 is biased, so the real extra protection is small.
5. **All AES is the best value.** It gives the same practical protection as layered at about 1/7 of the cost, and it has the least code that can go wrong.
6. **Complexity.** Layered needs three keys per item and nested decryption. We tested every bit position of a layered item (all rejected), the layer count, and the owner check.

Our recommendation:
- For real protection, use all AES.
- If every item must use all three ciphers, layered is the safer way to do it. It costs about 0.5 s more per signup, which a customer will not notice, and no item is left with a weak cipher.
- The per-type setup costs almost the same as all AES but leaves the KTP and payslip with weak ciphers. Its value is in comparing the ciphers on different kinds of data.
- The team picks the setting for the deployed app and states the reason in the report.

## 5. Tests

Run: `python -m unittest discover -s tests`

| Test | What it shows |
|---|---|
| Encrypt then decrypt, all ciphers, sizes 0 to 100 KB | Data comes back identical |
| Look for NIK and name inside the encrypted item | They are not visible |
| Encrypt the same data twice, and data with repeated blocks | Output is different each time, so no ECB-like pattern |
| Flip one bit at every position of an item | Every change is detected |
| Wrong user, wrong data type, wrong master key | Decryption is refused |
| Full flow through Flask, all 3 ciphers | Register, login, download gives the same SHA-256. Nothing readable in the DB or `storage/`. A damaged file gives HTTP 500. No token gives 401 |
| Default cipher per data type | Each stored item uses the cipher from section 4 |
| Layered mode: every bit position, wrong layer count, wrong user or data type, full Flask flow | All changes rejected, data comes back identical |

## 6. Evaluation

**Question.** For a digital bank that signs up customers online, which cipher fits, and does speed decide?

**What we measured and why.** Customers feel upload and download time. The bank feels CPU and memory when many people register at once. So we measured encrypt and decrypt time, speed in MB/s, extra size, peak memory, and whether the data comes back identical (SHA-256 checked on every run).

**How.** We timed the real app code (`ciphers.encrypt` and `ciphers.decrypt`) with the same library and machine for every cipher. Sizes: 1 KB profile, 500 KB KTP, 2 MB document, 20 MB video. Each test has 3 warm-up runs and 30 timed runs, in shuffled cipher order, and we report the median. We also tried random data and repeated text. The difference is at most 0.7%, so the content does not matter.

**Results** (20 MB video, Apple ARM laptop, Python 3.14, pycryptodome):

| Cipher | Encrypt | Decrypt | MB/s | One full registration |
|---|---|---|---|---|
| AES-GCM | 74 ms | 73 ms | 271 | 83 ms |
| DES-CTR + HMAC | 449 ms | 448 ms | 45 | 503 ms (6.1x AES) |
| RC4 + HMAC | 22 ms | 22 ms | 902 | 25 ms (0.3x AES) |
| Layered AES + DES + RC4 | 546 ms | 544 ms | 37 | 613 ms (7.4x AES) |

RC4 bias test: in 200,000 random keys, the 2nd output byte was 0 about 2.08 times more often than it should be (theory says about 2). After skipping the first 3072 bytes it was 1.00 times, which is normal.

**What the results mean.**
1. Speed does not decide. Uploading 20 MB at 10 Mbit/s takes about 16 s. AES adds 0.07 s (under 0.5%). DES adds 0.45 s (under 3%). Security decides, and the fastest cipher (RC4) is the one banned in TLS.
2. Speed matters on the server. DES needs 0.45 CPU-seconds per video, 6x AES. For 100 registrations at once that is 45 CPU-seconds against 7.4.
3. AES versus RC4 depends on the machine. This ARM laptop has no fast AES path in pycryptodome, so RC4 wins. On x86 with AES hardware support, AES is usually much faster. We did not measure that, so do not present it as a result.
4. The extra size is 47 to 55 bytes per item. It does not matter.
5. Memory peaks at about 3x the file size (original, encrypted copy, and one more copy). A 60 MB upload uses about 180 MB per request. This is fine for the project. A real system should process files in chunks. Ignore the 17x to 29x numbers for the 1 KB item. That is fixed Python overhead.
6. Security cannot be measured with a timer:
   - DES: 56-bit key. Stallings 4.4 (p. 134, Table 4.5): one PC breaks it in about a year, a supercomputer in about an hour.
   - RC4: biased output and a weak key setup (Stallings 8.5, p. 271). RFC 7465 bans it in TLS. Skipping bytes and using one key per item fixes the bias we measured, but RC4 is still not recommended.
   - AES-256-GCM: no known practical attack, and it checks integrity.

**Conclusion.** AES-256-GCM is the only cipher with no known weakness, so it protects the data that would hurt most if leaked. RC4 and DES are used because the assignment requires them: either on lower-harm data (per type) or as extra layers (layered). Section 4b compares the two ways. Any setup can be switched to AES with one setting.

**Limits of these results.** One machine, one library, and no network or disk in the timing. The memory tool only sees Python memory, so 3x is the minimum.

## 7. Comparison with the lab reference

Reference: `ukassu/lab-session-information-security` (`crypto_tool.py`).

| | Lab reference | This project | Why |
|---|---|---|---|
| Library | pycryptodome | pycryptodome | Same |
| AES | AES-256-CBC with padding | AES-256-GCM | Built-in integrity, no padding. CBC + HMAC was 71.6 ms vs 72.7 ms, so no speed reason for CBC |
| DES | DES-CBC with padding | DES-CTR + HMAC | CTR is 14% faster than CBC (447 vs 521 ms), no padding |
| RC4 | plain RC4 | RC4 + HMAC, first 3072 bytes skipped | Removes the start-of-stream bias and adds integrity |
| Integrity | none (their README says so) | tag or HMAC on every item | A wrong key or changed data is always caught, not just about 255 times in 256 |
| Key source | user password, PBKDF2, 600,000 rounds | `MASTER_KEY` + HKDF, random salt per item | See below |
| Nonce / IV | random each time | random each time | Same |
| Output | JSON with Base64 | raw bytes | Smaller, fits a BLOB column |

The key source is the one real design difference, and each choice has a trade-off:
- **Password-derived keys** (lab tool): the server cannot read the data without the user's password. This is safer if the server or `MASTER_KEY` is hacked. But PBKDF2 took 131 ms per key here (HKDF: 19 microseconds). Doing it for every item would add about 0.5 s per registration, more than all the AES work (83 ms). A password reset would also lose the data or force re-encryption.
- **Server master key** (ours): encryption stays cheap and password resets are safe. But the server can decrypt everything, so access control is the only thing limiting who reads data.
- **Middle option, not built:** one random key per user, locked with a key made from their password, and unlocked at login. This needs one PBKDF2 per login instead of per file, but adds work in `App.py`.

## 8. Questions for the TA

Answered: the TA said both readings of "each of the following ciphers" are fine (one cipher per data type, or all three layered), and asked us to compare them side by side. We did, in section 4b.

Still open:
1. Is AES-GCM accepted as the mode of operation? Our basis: Stallings 12.7 presents GCM as an authenticated mode built on CTR.
2. Should the key come from the user's password (like the lab tool), or is a server master key acceptable? "Only an authenticated user may get their own data back" can be read either way. See section 7.
