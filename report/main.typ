#import "@preview/ilm:2.1.1": *

#set text(lang: "en")

// Set to `true` once `benchmark_chart.png` is placed next to this file.
// (The chart was referenced via a local Windows path in report.md, so it is
// not bundled here.)
#let show-chart = false

#show: ilm.with(
  title: [Symmetric Encryption in a Mobile Banking Application],
  authors: "Group 22",
  // The report is limited to 2 A4 pages, so everything that adds pages
  // (cover, table of contents, chapter page breaks, bibliography, indices)
  // is switched off.
  cover-page: none,
  table-of-contents: none,
  chapter-pagebreak: false,
  footer: "page-number-center",
  external-link-circle: false,
)

// ── Compact layout to fit 2 pages ──────────────────────────────────────────
#set text(size: 10pt)
#set page(margin: (x: 2cm, top: 1.9cm, bottom: 1.8cm))
#set par(leading: 0.6em, spacing: 0.95em)
#show heading.where(level: 1): set text(size: 12.5pt)
#show heading.where(level: 1): set block(above: 1.2em, below: 0.6em)
#show raw.where(block: false): set text(size: 8.5pt)
#set table(inset: 5pt)
#set figure(gap: 0.5em)
#show figure.caption: set text(size: 8.5pt)
#set list(spacing: 0.7em, indent: 0.5em)

// ── Title block ────────────────────────────────────────────────────────────
#align(center)[
  #text(size: 16pt, weight: "bold")[Assignment 1 Report — Symmetric Encryption in a Mobile Banking Application]
  #v(-0.2em)
  *Group 22* · Repository: `rifaidh/InfoSec-Symmetric-Encryption-Group22`
]
#v(0.2em)

= Scenario

We built a *digital bank onboarding portal* — a Flask web application where customers register for a mobile banking account online. During registration, users submit personal data (full name, NIK, email, phone, date of birth, address), upload three documents (KTP scan — JPEG/PNG/PDF, a supporting office document such as a payslip — PDF/DOCX/XLSX, and a selfie video for e-KYC — MP4/WEBM), set a password, and consent to data processing under Indonesia's UU PDP No. 27/2022. After login, users can view their profile and download their own documents; no user can access another user's data.

*Why this scenario matters.* Indonesian banking regulations require Know-Your-Customer (KYC) identity verification. The stored data includes general personal data (name, NIK, address), special-category data under both UU PDP Pasal 4(2) and GDPR Art. 9 (biometric selfie video, personal financial documents), and scanned identity documents. A breach of this data enables identity theft, financial fraud, and irreversible biometric compromise. GDPR Art. 32(1)(a) explicitly names encryption as an appropriate technical safeguard, and UU PDP Pasal 35 requires security measures proportional to data sensitivity. Encrypting everything at rest ensures that a stolen database or file system yields nothing readable.

= Analysis: Cipher Performance Comparison

*What we measured.* Customers experience upload/download latency; the server experiences CPU load during bulk registrations. We therefore measured *encrypt and decrypt wall-clock time* (median of 30 runs, 3 warm-up, randomised cipher order), *throughput in MB/s*, *storage overhead in bytes*, and *peak memory* — for all three required ciphers (AES, DES, RC4) plus a layered mode (AES→DES→RC4). We tested four representative object sizes: 1 KB profile JSON, 500 KB KTP scan, 2 MB office document, and 20 MB selfie video, using both random and repetitive content.

*Why this analysis.* The assignment asks us to _evaluate how the three ciphers compare in practice_ and _decide what to measure, how to measure it reliably, and what the results tell you_. Timing and throughput directly answer "which cipher slows the user down?" Memory answers "does the server cope under load?" The random-vs-repetitive test checks that no cipher leaks patterns (an ECB-like weakness). We also measured RC4 keystream bias (2nd-byte test, 200~000 trials) and HKDF key-derivation cost.

*Key results* (Python 3.14, Apple ARM, pycryptodome; 20 MB video):

#figure(
  table(
    columns: (auto, auto, auto, auto, 1fr),
    align: (left, right, right, right, left),
    table.header[Cipher][Encrypt (ms)][Decrypt (ms)][MB/s][One full registration],
    [AES-256-GCM], [74], [73], [271], [83 ms],
    [DES-CTR + HMAC], [449], [448], [45], [503 ms (6.1× AES)],
    [RC4-drop + HMAC], [22], [22], [902], [25 ms (0.3× AES)],
    [Layered AES+DES+RC4], [546], [544], [37], [613 ms (7.4× AES)],
  ),
  caption: [Encryption cost for a 20 MB selfie video.],
)

#if show-chart [
  #figure(
    image("benchmark_chart.png", width: 100%, height: 5.6cm, fit: "contain"),
    caption: [Throughput comparison across object sizes and ciphers (log scale).],
  )
]

*Interpretation.* (1) Speed does not determine the choice. Uploading 20 MB at 10~Mbit/s takes \~16~s; AES adds 0.07~s (\<0.5%), DES adds 0.45~s (\<3%). Security decides. (2) RC4 is fastest on this ARM machine (no AES-NI), but is banned in TLS (RFC 7465) due to output bias. (3) Random vs. repetitive content differs by ≤0.7% — no cipher leaks patterns. (4) RC4 2nd-byte bias is 2.08× ideal without drop; after dropping 3~072 bytes it is 1.00×. (5) Storage overhead is 47–156 bytes per object — negligible. (6) Memory peaks at \~3× object size.

= Design Justifications

*Architecture: Flask + SQLite.* The scenario is a server-rendered web app with a REST API. Flask is minimal, sufficient for the KYC flow, and lets us focus on cryptography rather than framework complexity. SQLite stores metadata; encrypted files live on disk as `.bin` blobs.

*Mode choices — no ECB.*
- _AES-256-GCM:_ GCM provides authenticated encryption (Stallings §12.7) — confidentiality and integrity in one pass, no padding. AES-CTR+HMAC was 14% faster but requires manually combining encryption and MAC; GCM is a standard construction with fewer things to get wrong.
- _DES-CTR + HMAC-SHA256:_ CTR is the fastest DES mode we measured (447 ms vs. CBC 521 ms for 20 MB), needs no padding, and permits streaming. Since DES has no authenticated mode, we add encrypt-then-MAC with HMAC-SHA256.
- _RC4 (drop 3~072) + HMAC-SHA256:_ RC4 is a stream cipher with no modes. We skip the first 3~072 bytes to eliminate the well-known initial keystream bias (confirmed by our test). HMAC-SHA256 provides integrity.
- _ECB is never used_ — not in the application, tests, or benchmarks.

*Key handling: HKDF per object.* A single `MASTER_KEY` (from an environment variable) is expanded via HKDF-SHA256 with a fresh 16-byte random salt, the cipher name, `user_id`, and data purpose as context. This gives every stored object its own unique key (cost: 19~µs), preventing nonce reuse across objects — critical for GCM, CTR, and RC4. The tag/HMAC additionally binds to `user_id` and purpose, so copying a blob to another user or document type fails integrity checks.

*Cipher-per-data-type policy.* We assign ciphers by data sensitivity: AES-GCM for profile and selfie video (highest harm — biometric and full identity), RC4+HMAC for office documents (medium harm — financial), DES-CTR+HMAC for KTP scans (lowest marginal harm — same fields exist in the encrypted profile, and KTP copies are widely shared). Cost: 87 ms per registration vs. 83 ms for all-AES — effectively identical. We also support a *layered mode* (`CIPHER=layered`) where every object is encrypted with all three ciphers sequentially (AES inside DES inside RC4, each with independent keys). Layered costs 613 ms (7.4× all-AES) but ensures no single-cipher weakness can expose any object. Both configurations are tested and switchable via a single environment variable.

*Storage: encrypted files on disk, HMAC lookups in the database.* Email and NIK are never stored in plaintext; keyed HMAC digests serve as lookup indices for login and duplicate checking. Passwords are hashed with Werkzeug's `generate_password_hash` (not encrypted). On download, the server re-computes SHA-256 of the decrypted file and rejects it if the hash does not match the stored value — a second integrity layer on top of the cryptographic tag.

*Known limitations.* DES (56-bit key) and RC4 are cryptographically weak and used only because the assignment requires all three ciphers. In production, `CIPHER=aes` switches everything to AES-256-GCM. The `MASTER_KEY` resides on the application server; a dedicated key management service would improve security but is out of scope.
