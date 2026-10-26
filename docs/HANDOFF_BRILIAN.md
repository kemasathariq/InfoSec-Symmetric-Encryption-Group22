# Handoff to Brilian: backend, database, deploy

The security part is done and tested: data classification, encryption and benchmark. Your job is to turn the project into a clean, working, deployed app without breaking the security part.

Start here: `git checkout main && git pull`, then follow this file from the top.

## Who owns what

| File | Owner |
|---|---|
| `BE/ciphers.py`, `BE/Hooks.py` | Security, done. Do not change the behaviour |
| `BE/App.py`, `BE/DB.py` | You |
| `FE/` | Rifai |
| `tests/` | Shared, must keep passing |
| `bench/`, `docs/` | Security, done |

## Rules to keep

1. Every private value goes through `hooks.protect(data, user_id=..., purpose=...)` before saving, and `hooks.unprotect(...)` after reading. Use the same `user_id` and `purpose` for both. If you change a user's ID or rename a purpose (`profile`, `ktp`, `supporting_doc`, `selfie_video`), old data can no longer be decrypted.
2. `protect()` returns raw bytes. Save them as they are (BLOB, BYTEA or a storage file). Do not decode or trim them. If a column needs text, use base64 on the database side.
3. Keep the SHA-256 check after `unprotect` in `download_document`.
4. Keep every document query filtered by the `user_id` from the session.
5. Never log or cache plain data.
6. `ciphers.IntegrityError` must stay a server error (500). Do not catch and ignore it.
7. Keep the file names `App.py`, `DB.py`, `Hooks.py` and the imports `import DB as db`, `import Hooks as hooks`. They work on macOS and Linux. New files are lowercase, like `ciphers.py`.

## Setup

    pip install -r requirements.txt
    cp .env.example .env        # fill in the two keys (see the file)
    # The app does not read .env by itself. Either export the values in your
    # terminal, or add python-dotenv and load .env in config.py (to do, step 2).
    cd BE && python App.py
    # from the repo root:
    python -m unittest discover -s tests

| Setting | What it does | Note |
|---|---|---|
| `MASTER_KEY` | The root of all encryption keys | Required. If you lose it, all data is unreadable. Keep it in a secret manager, not in git |
| `LOOKUP_KEY` | HMAC key for `email_lookup` and `nik_lookup` | Required, and different from `MASTER_KEY` |
| `CIPHER_POLICY` | Optional. Change the cipher of single data types, e.g. `ktp=aes,supporting_doc=aes` | Default: profile and video AES, document RC4, KTP DES (`docs/CRYPTO_DESIGN.md` section 4) |
| `CIPHER` | Optional. `aes`, `des` or `rc4` for everything | Use `aes` in production |
| `DB_PATH`, `STORAGE_DIR` | Where data is saved | Must be on storage that is kept between restarts |

## Target structure

```
repo/
  BE/
    App.py          routes only
    DB.py           schema and connection
    Hooks.py        protect / unprotect (same signature)
    ciphers.py      the crypto (do not change)
    config.py       NEW: reads settings, stops the app if a key is missing
  FE/               Rifai's pages (templates, static)
  tests/            keep passing
  bench/            done
  docs/             done
  .env.example      done (template, no real secrets)
  requirements.txt  add gunicorn
  .gitignore        done (ignores .env, *.db, storage/)
```

You may split `App.py` into more files if it helps, but keep rules 1 to 7 and keep the tests passing. If you rename or move modules, update `load_app()` in `tests/test_app_e2e.py` to match.

## To do, in order

**1. Clean up after the merge with Rifai's branch.**
- Check no database is in git: `git ls-files | grep -i "\.db"` must print nothing. If it prints `BE/mbanking.db`, run `git rm --cached BE/mbanking.db`.
- The `/lumio` route uses `lumio.html`, which does not exist, so it returns 500. Remove the route or add the file.
- Click through the whole frontend once (register, login, view profile, download each file) and report any bug to Rifai.

**2. Make keys required (`config.py`).**
- `App.py` has a default `LOOKUP_KEY` (`dev-only-change-me`). Remove it. Stop the app at startup if `LOOKUP_KEY` or `MASTER_KEY` is missing.
- `ciphers.py` falls back to a dev `MASTER_KEY` when none is set. Add a check that refuses to start when `APP_ENV=production` and the key is missing. This is the only change allowed in `ciphers.py`. Add a test for it.

**3. Fix the plain-data leaks** (`docs/DATA_CLASSIFICATION.md`, issues 1 to 3).
- Stop saving `documents.original_name` as plain text. Easiest: remove it and use a generic download name like `ktp.jpg`.
- Account number and balance are plain columns. Either move them into the encrypted profile, or leave them and tell Kema, so the report lists it as a known limit.

**4. Production server and security basics.**
- Remove `app.run(debug=True)` before deploying, because the Flask debugger lets people run code. Use gunicorn (add it to `requirements.txt`).
- Use HTTPS on the deployed site.
- Limit login and register attempts (not built yet).
- Add CORS only if the frontend ends up on another domain.
- Delete expired rows from `sessions`.

**5. Pick a host and deploy.** SQLite and local files need a disk that keeps its data.
- Do not use Vercel or other serverless hosts. Their disk is not permanent, and the request size limit (about 4.5 MB) is below our 60 MB video limit.
- Use Render, Railway, Fly.io, or a VPS with a volume. Or move to Postgres plus file storage.
- On Supabase, still encrypt in our app before uploading. The assignment grades our own implementation, not the provider's. Save the `protect()` output as `BYTEA` or a storage file.
- Each request uses about 3x the upload size in memory. Limit the number of workers to fit the RAM.
- Set `MASTER_KEY` and `LOOKUP_KEY` in the host's secret settings. Keep a safe backup of `MASTER_KEY`.

**6. Update the README.** Add the real deployed URL, how to run locally, and the test command.

**7. Tell Kema** the final list of what is encrypted and what is not, and the deployed link. Kema puts both in the report.

## Done when

1. `python -m unittest discover -s tests` passes.
2. The app is deployed on a public link, with HTTPS, and a new user can register with an image, a PDF and a video, log in, and download all three unchanged.
3. After registering on the deployed app, `SELECT profile FROM users` and the `storage/` files show no readable name or NIK (check with `strings` or `grep`).
4. User B cannot download user A's documents.
5. Copying A's `.bin` file over B's path and downloading as B gives an integrity error (500), not A's data.
6. `git ls-files` shows no `.db` file, no `.env`, and no `storage/` files.
7. The app refuses to start when `MASTER_KEY` or `LOOKUP_KEY` is missing in production.
