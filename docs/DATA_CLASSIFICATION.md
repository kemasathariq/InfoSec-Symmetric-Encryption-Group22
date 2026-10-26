# Data Classification (UU PDP 27/2022 and GDPR)

This file decides which data is private, why, and how we protect it.

## Where the article numbers come from

- **UU PDP:** read in the official PDF (50 pages) from [peraturan.bpk.go.id](https://peraturan.bpk.go.id/Details/229798/uu-no-27-tahun-2022). The PDF is a scan, so a few words are garbled. Every UU PDP article below was found in it, except where marked "not found".
- **GDPR:** Art. 4(1), 4(14), 5(1)(c), 5(1)(f), 9(1), 32(1)(a), 33(1) and the title of Art. 34 were read on [gdpr-info.eu](https://gdpr-info.eu). The other GDPR numbers (Art. 6, 7, 17, 25, 35, Recitals 26 and 51) were not opened. They are marked "not checked".
- **OJK KYC regulation:** name not checked.
- Stallings does not cover regulation.

## Legal basis

| Topic | UU PDP (checked) | GDPR |
|---|---|---|
| What is personal data | Pasal 1 angka 1 | Art. 4(1), checked |
| General personal data | Pasal 4(3): full name, gender, nationality, religion, marital status, data combined to identify a person | Art. 4(1), checked |
| Specific / special data | Pasal 4(2): health, biometric, genetic, crime record, children, personal financial (see note), other data by law | Art. 9(1) and 4(14), checked |
| Legal basis, consent | Pasal 20(2)(a) explicit consent. Pasal 20(2)(c) legal duty of the controller. Pasal 21: what must be told to the person | Art. 6(1)(a), 7: not checked |
| Collect only what is needed | Pasal 16(2)(a): "terbatas dan spesifik" (limited and specific) | Art. 5(1)(c), checked |
| Duty to keep data secure | Pasal 35: (a) technical measures, (b) set the security level by the nature and risk of the data. Pasal 36: keep it confidential. Pasal 39(1): prevent unauthorised access | Art. 5(1)(f) and 32(1)(a), checked |
| Telling people about a leak | Pasal 46(1): in writing within 3x24 hours, to the person and to the agency | Art. 33(1): 72 hours, checked |
| Risk assessment | Pasal 34(1), and 34(2)(b) says processing specific data counts as high risk | Art. 35: not checked |
| Delete data, withdraw consent | Pasal 8 (end processing, delete), Pasal 9 (withdraw consent), Pasal 40 (stop within 3x24 hours of withdrawal) | Art. 17, 7(3): not checked |

Notes on the table:
- **Pasal 4(2) item f.** The scanned PDF is garbled at this item. Other sources write it as "data keuangan pribadi" (personal financial data). Look at page 5 of the PDF yourself before quoting it.
- **Pasal 22 was not found** in the scan, so we do not cite it.
- **Pasal 35(b)** supports choosing the security level by risk. This is the legal basis for matching cipher strength to data harm. It does not make a weak cipher like DES acceptable for any private data.
- **Pasal 34(2)(b)** means our app would need an impact assessment in real life, because it processes specific data (biometric, financial). We do not build one. List it as out of scope.

Two points matter for our encryption design:
1. GDPR Art. 32(1)(a) names encryption as a proper security measure.
2. GDPR Art. 34(3)(a): if leaked data cannot be read (for example because it is encrypted), the company does not have to warn the affected people. **UU PDP Pasal 46 has no such exception.** In Indonesia the bank must still notify within 3x24 hours. Encryption still reduces the real harm, but do not say it removes the duty to notify.

## What we treat as private

Private means personal data (general or specific), passwords, and anything that identifies a person when combined with other data. Private data must stay unreadable even if someone copies the database or the `storage/` folder.

| Data | Type | Private | Why | How we protect it |
|---|---|---|---|---|
| Full name, birth date, address | General | Yes | Directly identifies a person | Encrypted (profile) |
| NIK | General, national ID number | Yes | With name and birth date, enough for identity theft | Encrypted, HMAC used for lookup |
| Email, phone | General | Yes | Used for phishing and account takeover | Encrypted, HMAC used for email lookup |
| KTP scan | ID document | Yes | Has NIK, photo and address together | Encrypted file |
| Office document (payslip) | Personal financial, specific | Yes | Shows income and employer | Encrypted file |
| Selfie video | Biometric, specific | Yes | Cannot be replaced if leaked. GDPR Recital 51 (not checked): a photo counts as biometric when used to identify someone, and e-KYC does that | Encrypted file |
| Password | Login secret | Yes | Must never be readable | Hashed (werkzeug), not encrypted |
| Account number, balance | Personal financial, specific | Yes | Financial identity | Access control only (see issue 1) |
| `documents.original_name` | May contain a name | Yes | Text typed by the user | See issue 2 |
| `email_lookup`, `nik_lookup` | Pseudonymised (GDPR Recital 26, not checked) | Yes | NIK has a fixed format, so it is easy to guess if the HMAC key leaks | HMAC with its own key |
| `mime`, `size`, `created_at`, `consent_at` | Metadata | No | Low risk on their own | Plain |

## Open issues in the current code

1. **Account number and balance are plain columns.** Balance is always 0 (transactions are out of scope) and the account number is used to check for duplicates. Either move both into the encrypted profile, or list this as a known limit in the report.
2. **`documents.original_name` is plain.** File names often contain a person's name. Easiest fix: do not store it and use a generic download name like `ktp.jpg`. This also fits data minimisation (Pasal 16(2)(a), GDPR Art. 5(1)(c)).
3. **`LOOKUP_KEY` has a default value** (`dev-only-change-me`) in `App.py`. With the default, anyone with the database can guess every NIK offline. It must be set when deploying and must differ from `MASTER_KEY`.

## Consent and minimisation

- We only collect KYC data. The legal reason for collecting KTP and selfie is the bank's KYC duty (Pasal 20(2)(c): legal duty), not only consent. The name of the OJK regulation is not checked.
- `consent_pdp` must be ticked and `consent_at` is saved with the time (Pasal 20(2)(a)).
- Right of access is covered by `/api/me`. Deleting data and withdrawing consent (Pasal 8, 9, 40) are out of scope (PRD section 13).

## How this maps to code

| Decision | How |
|---|---|
| Encrypted profile | `hooks.protect(json, purpose="profile")` |
| Encrypted file | `hooks.protect(bytes, purpose="ktp" / "supporting_doc" / "selfie_video")` |
| Hashed password | `generate_password_hash` |
| Users cannot read each other's data | `user_id` and `purpose` are part of every stored item's tag |
