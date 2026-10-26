import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    email_lookup   TEXT UNIQUE NOT NULL,  -- HMAC(email), untuk login tanpa menyimpan email polos sebagai kunci
    nik_lookup     TEXT UNIQUE NOT NULL,  -- HMAC(NIK), untuk cek duplikat
    password_hash  TEXT NOT NULL,
    profile        BLOB NOT NULL,         -- JSON data pribadi (nanti dilindungi hooks.protect)
    cipher         TEXT NOT NULL DEFAULT 'none',
    account_number TEXT UNIQUE NOT NULL,
    balance        INTEGER NOT NULL DEFAULT 0,
    consent_at     TEXT NOT NULL,         -- persetujuan pemrosesan data (UU PDP / GDPR)
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    kind          TEXT NOT NULL,          -- ktp | supporting_doc | selfie_video
    original_name TEXT NOT NULL,
    mime          TEXT NOT NULL,
    path          TEXT NOT NULL,
    size          INTEGER NOT NULL,       -- ukuran file asli (plaintext)
    sha256        TEXT NOT NULL,          -- hash file asli, untuk cek integritas saat diunduh
    cipher        TEXT NOT NULL DEFAULT 'none',
    created_at    TEXT NOT NULL,
    UNIQUE (user_id, kind)
);

CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        get_db().executescript(SCHEMA)
