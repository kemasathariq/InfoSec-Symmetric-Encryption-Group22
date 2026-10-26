# Data Classification (UU PDP 27/2022 and GDPR)

This file decides which data is private, why, and how we protect it.

Checking status of the article numbers:
- Checked against the source: GDPR Art. 32(1)(a) and Art. 34 (gdpr-info.eu).
- Confirmed by secondary sources: UU PDP Art. 4 (specific data includes health, biometric, genetic, criminal record, children, personal financial).
- Everything else comes from memory and is not checked. Stallings does not cover regulation. Open the official text and check each item marked (verify) before it goes in the report.

## Legal basis

| Topic | UU PDP | GDPR |
|---|---|---|
| What is personal data | Art. 1(1) | Art. 4(1) |
| General personal data | Art. 4(3) | Art. 4(1) |
| Specific / special data (biometric, personal financial) | Art. 4(2) | Art. 9(1), Art. 4(14) |
| Consent | Art. 20-22 (verify) | Art. 6(1)(a), Art. 7 |
| Duty to keep data secure | Art. 35, 36, 39 (verify) | Art. 5(1)(f), 25, 32(1)(a) |
| Telling people about a leak | Art. 46, within 3x24 hours (verify) | Art. 33 (72 hours), Art. 34 |
| Risk assessment | Art. 34 (verify) | Art. 35 |
| Deleting data, withdrawing consent | Art. 8, 9 (verify) | Art. 17, 7(3) |

Two points matter for our encryption design:
1. GDPR Art. 32(1)(a) names encryption as a proper security measure.
2. GDPR Art. 34(3)(a): if leaked data cannot be read (for example because it is encrypted), the company does not have to warn the affected people. So encryption turns a stolen disk or database into a much smaller incident.

## What we treat as private

Private means personal data (general or specific), passwords, and anything that identifies a person when combined with other data. Private data must stay unreadable even if someone copies the database or the `storage/` folder.

| Data | Type | Private | Why | How we protect it |
|---|---|---|---|---|
| Full name, birth date, address | General | Yes | Directly identifies a person | Encrypted (profile) |
| NIK | General, national ID number | Yes | With name and birth date, enough for identity theft | Encrypted, HMAC used for lookup |
| Email, phone | General | Yes | Used for phishing and account takeover | Encrypted, HMAC used for email lookup |
| KTP scan | ID document | Yes | Has NIK, photo and address together | Encrypted file |
| Office document (payslip) | Personal financial, specific | Yes | Shows income and employer | Encrypted file |
| Selfie video | Biometric, specific | Yes | Cannot be replaced if leaked. GDPR Recital 51: a photo counts as biometric when used to identify someone, and e-KYC does that | Encrypted file |
| Password | Login secret | Yes | Must never be readable | Hashed (werkzeug), not encrypted |
| Account number, balance | Personal financial, specific | Yes | Financial identity | Access control only (see issue 1) |
| `documents.original_name` | May contain a name | Yes | Text typed by the user | See issue 2 |
| `email_lookup`, `nik_lookup` | Pseudonymised (GDPR Recital 26) | Yes | NIK has a fixed format, so it is easy to guess if the HMAC key leaks | HMAC with its own key |
| `mime`, `size`, `created_at`, `consent_at` | Metadata | No | Low risk on their own | Plain |

## Open issues in the current code

1. **Account number and balance are plain columns.** Balance is always 0 (transactions are out of scope) and the account number is used to check for duplicates. Either move both into the encrypted profile, or list this as a known limit in the report.
2. **`documents.original_name` is plain.** File names often contain a person's name. Easiest fix: do not store it and use a generic download name like `ktp.jpg`. This also fits data minimisation (UU PDP Art. 16, GDPR Art. 5(1)(c), verify).
3. **`LOOKUP_KEY` has a default value** (`dev-only-change-me`) in `App.py`. With the default, anyone with the database can guess every NIK offline. It must be set when deploying and must differ from `MASTER_KEY`.

## Consent and minimisation

- We only collect KYC data. The legal reason for collecting KTP and selfie is the bank's KYC duty under OJK rules (name of the regulation: verify), not only consent.
- `consent_pdp` must be ticked and `consent_at` is saved with the time.
- Right of access is covered by `/api/me`. Deleting data and withdrawing consent are out of scope (PRD section 13).

## How this maps to code

| Decision | How |
|---|---|
| Encrypted profile | `hooks.protect(json, purpose="profile")` |
| Encrypted file | `hooks.protect(bytes, purpose="ktp" / "supporting_doc" / "selfie_video")` |
| Hashed password | `generate_password_hash` |
| Users cannot read each other's data | `user_id` and `purpose` are part of every stored item's tag |
