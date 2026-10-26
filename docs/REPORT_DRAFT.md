# DRAFT, do not submit as is
Starting point only. Rewrite it in your own words, check every number against `bench/results.md` and `bench/modes.md`, and check every article number (marked [verify]) against the official text. Limit: 2 A4 pages. Paste into Word or Docs at 10-11 pt with normal margins, then check the page count.

---

# Protecting Customer Data in a Digital Bank Signup (Group 22)

## 1. Scenario and why the app is useful

A digital bank opens accounts fully online, with no branch visit (e-KYC). To sign up, a customer sends their name, NIK, birth date, address, email, phone, a KTP scan, a payslip and a selfie video. Together these are enough for identity theft or a fake loan application. The selfie video is biometric data, so it cannot be changed after a leak.

Databases and file storage are the usual place where leaks happen. So our app encrypts everything private before it is stored, and gives it back, unchanged, only to the logged-in owner. This also helps the bank legally: under GDPR Art. 34(3)(a) [verify], a bank does not have to warn customers about a leak if the stolen data is unreadable.

## 2. Which data is private

We based this on UU PDP 27/2022 Art. 4 (general vs specific personal data) and GDPR Art. 4 and 9 [verify article numbers].

- **Encrypted:** profile (name, NIK, birth date, address, email, phone), KTP scan, payslip, selfie video. Biometric and personal financial data are "specific" data in UU PDP, and biometric data is a special category in GDPR.
- **Hashed, not encrypted:** password, because it never needs to be read back.
- **Not encrypted (known limit):** account number, balance and file metadata. See section 5.

## 3. Design decisions and reasons

| Decision | Reason |
|---|---|
| One pair of functions, `protect()` and `unprotect()`, used for all private data | No private data can skip encryption, and all ciphers share one code path, so the comparison is fair |
| Each data type has its own cipher: profile and video use AES-GCM, payslip uses RC4, KTP uses DES | The assignment needs all three ciphers. The worse a leak would be, the stronger the cipher. KTP fields are also in the encrypted profile, so KTP is the lowest-harm item |
| AES-256 in **GCM** mode | Encrypts and checks integrity in one step (Stallings 12.7). CTR + HMAC was 14% faster, about 10 ms on 20 MB, which nobody notices |
| DES in **CTR** mode + HMAC-SHA256 | DES has no built-in integrity mode. CTR was the fastest DES mode we tested (447 ms vs 521 ms for CBC) and needs no padding (Stallings 7.6) |
| RC4 + HMAC-SHA256, first 3072 bytes skipped | RC4 has no modes and no integrity check. The first bytes of its output are biased, so we skip them |
| No ECB, and no CBC | ECB gives identical ciphertext for identical blocks (Stallings 7.2). CBC has no integrity check, needs padding and encrypts one block at a time. It gave no speed gain (71.6 ms vs 72.7 ms for GCM) |
| One key per stored item: HKDF from `MASTER_KEY`, a random salt, the user ID and the data type | A key and nonce are never reused, a leaked key exposes one item, and the tag stops an item being copied to another user |
| A tag or HMAC on every item, plus SHA-256 of the original file | Any changed bit is rejected (tested at every position). The SHA-256 proves the download is identical |
| Passwords hashed; email and NIK found through HMAC | Login and duplicate checks still work after email and NIK are encrypted |
| Flask + SQLite, files saved under random names | Enough for the project scale and easy to reproduce. Random names stop file names leaking identity |

## 4. Evaluation: do the ciphers differ in practice?

**Question.** Which cipher fits a signup flow, and does speed decide?
**Why this analysis.** Customers feel upload time, and the bank feels server CPU and memory when many people sign up at once.
**Method.** We timed the real app code (`ciphers.encrypt` and `ciphers.decrypt`) on the same laptop (Apple ARM, Python 3.14, pycryptodome). Sizes were 1 KB profile, 500 KB KTP, 2 MB payslip and 20 MB video, with random and repeated data. Each test used 3 warm-up and 30 timed runs, in shuffled cipher order. We report the median and checked every result with SHA-256.

| Cipher | 20 MB video | Speed | One full signup (all 4 files) |
|---|---|---|---|
| AES-GCM | 74 ms | 272 MB/s | 83 ms |
| DES-CTR + HMAC | 449 ms | 45 MB/s | 503 ms (6.1x AES) |
| RC4 + HMAC | 22 ms | 906 MB/s | 25 ms (0.3x AES) |

**What it means.**
1. **Speed does not decide.** Uploading 20 MB at 10 Mbit/s takes about 16 s. Encryption adds 0.07 s with AES and 0.45 s with DES.
2. **Speed matters on the server.** DES needs 6x the CPU of AES. With 100 signups at once, that is 45 CPU-seconds against 7.4.
3. **The fastest cipher is the unsafe one.** RC4 won here, but it is banned in TLS (RFC 7465). Its second output byte was 0 about 1.94 times more often than it should be, and 1.01 times after we skipped the first 3072 bytes. DES has a 56-bit key that one PC can break in about a year (Stallings 4.4).
4. **The ranking depends on the machine.** This laptop has no fast AES path in the library. On x86 with AES hardware support, AES is usually much faster. We did not measure this.

**Conclusion.** AES-256-GCM is the only cipher without a known weakness, so it protects the most damaging data (profile and biometric video). We use DES and RC4 only on lower-harm data because the assignment requires them. For real use, all data should use AES: one setting changes it.

## 5. Known limits

- DES on the KTP only stops casual access: a 56-bit key can be searched, and a known file header makes a guess easy to check.
- `MASTER_KEY` is on the same server as the data. If the server is hacked, the key is too. A key management service would fix this.
- Account number, balance and file metadata are not encrypted [update if Brilian fixes this].
- A 60 MB upload uses about 180 MB of memory, because files are processed whole. A real system would process them in chunks.
- Timings come from one machine and one library, with no network or disk in the timing.

*Sources: Stallings, Cryptography and Network Security, 7th ed., sections 4.4, 7.2, 7.3, 7.6, 8.5, 12.7. Code and full results: GitHub repository, `docs/CRYPTO_DESIGN.md`, `bench/`.*

*AI use: [add the conversation link and screenshot here, as the assignment requires.]*
