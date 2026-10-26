# DRAFT, do not submit as is
Starting point only. Rewrite it in your own words, check every number against `bench/results.md` and `bench/modes.md`, and fill the [brackets]. Limit: 2 A4 pages. Paste into Word or Docs at 10-11 pt, then check the page count. If it is too long, cut the "not encrypted" bullet and shorten the design table first.

---

# Protecting Customer Data in a Digital Bank Signup (Group 22)

## 1. Scenario and why the app is useful

A digital bank opens accounts fully online, with no branch visit (e-KYC). To sign up, a customer sends their name, NIK, birth date, address, email, phone, a KTP scan, a payslip and a selfie video. Together these are enough for identity theft or a fake loan application. The selfie video is biometric data, so it cannot be changed after a leak.

Databases and file storage are the usual place where leaks happen. So our app encrypts everything private before it is stored, and gives it back, unchanged, only to the logged-in owner. Encryption also limits the damage of a leak. Under GDPR Art. 34(3)(a) a company need not warn customers if the stolen data is unreadable. UU PDP Pasal 46 has no such exception, so the bank would still have to notify, but nothing readable would be lost.

## 2. Which data is private

Basis: UU PDP Pasal 4(2) lists biometric and personal financial data as "specific" personal data, and Pasal 4(3) lists name and combined identifying data as "general". GDPR Art. 9(1) treats biometric data as a special category. Pasal 35(b) asks the controller to set the security level by the nature and risk of the data.

- **Encrypted:** profile (name, NIK, birth date, address, email, phone), KTP scan, payslip, selfie video.
- **Hashed, not encrypted:** password, because it never needs to be read back.
- **Not encrypted:** [account number, balance, file metadata: update after Brilian's work]. See section 5.

## 3. Design decisions and reasons

| Decision | Reason |
|---|---|
| One pair of functions, `protect()` and `unprotect()`, for all private data | No private data can skip encryption, and every cipher shares one code path, so the comparison is fair |
| Two setups for the three ciphers, switched by one setting: **per data type** (profile and video AES, payslip RC4, KTP DES) or **layered** (AES, then DES, then RC4 on every item) | The assignment can be read both ways, so we built both and compare them in section 4 |
| AES-256 in **GCM** mode | Encrypts and checks integrity in one step (Stallings 12.7). CTR + HMAC was 14% faster, about 10 ms on 20 MB, which nobody notices |
| DES in **CTR** mode + HMAC-SHA256 | DES has no built-in integrity mode. CTR was the fastest DES mode (447 ms vs 521 ms for CBC) and needs no padding (Stallings 7.6) |
| RC4 + HMAC-SHA256, first 3072 bytes skipped | RC4 has no modes and no integrity check, and its first output bytes are biased |
| No ECB, no CBC | ECB repeats ciphertext for repeated blocks (Stallings 7.2). CBC has no integrity check, needs padding, encrypts block by block, and gave no speed gain (71.6 ms vs 72.7 ms for GCM) |
| One key per stored item (HKDF from `MASTER_KEY`, random salt, user ID, data type) | A key and nonce are never reused, one leaked key exposes one item, and the tag stops an item being copied to another user |
| A tag or HMAC on every item, plus SHA-256 of the original file | Any changed bit is rejected (tested at every position). The SHA-256 proves a download is identical |
| Passwords hashed; email and NIK found through HMAC | Login and duplicate checks still work after email and NIK are encrypted |
| Flask + SQLite, files under random names | Enough for the project scale. Random names stop file names leaking identity |

## 4. Evaluation: do the ciphers and setups differ in practice?

**Question.** Which cipher and which setup fit a signup flow, and does speed decide?
**Why this analysis.** Customers feel upload time. The bank feels server CPU and memory when many people sign up at once. Security cannot be timed, so we also compare how well each item is protected.
**Method.** We timed the real app code on one laptop (Apple ARM, Python 3.14, pycryptodome) with 1 KB, 500 KB, 2 MB and 20 MB files, random and repeated data, 3 warm-up and 30 timed runs in shuffled order. We report the median and checked every result with SHA-256.

| Cipher (20 MB video) | Encrypt | Speed |
|---|---|---|
| AES-GCM | 74 ms | 271 MB/s |
| DES-CTR + HMAC | 448 ms | 45 MB/s |
| RC4 + HMAC | 22 ms | 902 MB/s |
| Layered AES + DES + RC4 | 546 ms | 37 MB/s |

| One full signup (4 files) | Time | vs all-AES | Weakest protection of any item |
|---|---|---|---|
| All AES | 83 ms | 1.0x | AES |
| One cipher per data type | 87 ms | 1.0x | DES (the KTP) |
| Layered | 613 ms | 7.4x | all three layers must be broken |

**What it means.**
1. **Speed does not decide.** Uploading 20 MB at 10 Mbit/s takes about 16 s. Even layered adds only 0.5 s. On the server it matters more: 100 signups at once cost 61 CPU-seconds layered, against 8.7 per type and 8.3 all-AES.
2. **The fastest cipher is the unsafe one.** RC4 won, but it is banned in TLS (RFC 7465). Its 2nd output byte was 0 about 2.08 times too often, and 1.00 times after skipping 3072 bytes. DES has a 56-bit key that one PC can break in about a year (Stallings 4.4).
3. **Per type vs layered.** Per type costs the same as all-AES but leaves the KTP with DES and the payslip with RC4. Layered puts AES inside every item, so none is weaker than AES, for about 0.5 s more per signup. But the DES and RC4 layers add little on top of AES, and all-AES gives the same practical protection for 1/7 of the cost.
4. **The ranking depends on the machine.** This laptop has no fast AES path in the library. On x86 with AES hardware support, AES is usually much faster. We did not measure it.

**Conclusion.** For real protection, use all AES. Since the assignment needs all three ciphers, we [choose layered / choose per type: pick one and say why]. Layered is the safer way to use all three on every item. Per type is the cheaper way to compare the ciphers on different data.

## 5. Known limits

- DES alone (per-type KTP) only stops casual access: a 56-bit key can be searched, and a known file header makes a guess easy to check.
- `MASTER_KEY` is on the same server as the data. If the server is hacked, the key is too. A key management service would fix this.
- [Account number, balance and file metadata are not encrypted: update.]
- A 60 MB upload uses about 180 MB of memory (240 MB layered), because files are processed whole.
- We did not do the impact assessment that UU PDP Pasal 34 requires for specific data.
- Timings come from one machine and one library, with no network or disk in the timing.

*Sources: Stallings, Cryptography and Network Security, 7th ed., sections 4.4, 7.2, 7.3, 7.6, 8.5, 12.7. UU 27/2022 (peraturan.bpk.go.id). GDPR (gdpr-info.eu). Code and full results: GitHub repository, `docs/CRYPTO_DESIGN.md`, `bench/`.*

*AI use: [add the conversation link and screenshot here, as the assignment requires.]*
