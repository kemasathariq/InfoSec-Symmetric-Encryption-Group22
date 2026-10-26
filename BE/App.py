import hashlib
import hmac
import io
import json
import mimetypes
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request, send_file
from werkzeug.security import check_password_hash, generate_password_hash

import ciphers
import DB as db
import Hooks as hooks

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = Path(os.environ.get("STORAGE_DIR", BASE_DIR / "storage"))
LOOKUP_KEY = os.environ.get("LOOKUP_KEY", "dev-only-change-me").encode()
SESSION_HOURS = 24

ALLOWED_FILES = {
    "ktp": {".jpg", ".jpeg", ".png", ".pdf"},
    "supporting_doc": {".pdf", ".doc", ".docx", ".xls", ".xlsx"},
    "selfie_video": {".mp4", ".webm", ".mov"},
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^(\+62|62|0)8\d{8,12}$")

app = Flask(
    __name__,
    template_folder=str(BASE_DIR.parent / "FE" / "templates"),
    static_folder=str(BASE_DIR.parent / "FE" / "static"),
)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
app.config["DB_PATH"] = os.environ.get("DB_PATH", str(BASE_DIR / "mbanking.db"))
db.init_db(app)


# ---------- helpers ----------
def now():
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.isoformat(timespec="seconds")


def lookup_hash(value: str) -> str:
    return hmac.new(LOOKUP_KEY, value.encode(), hashlib.sha256).hexdigest()


def err(message, status, **extra):
    return jsonify({"error": message, **extra}), status


@app.errorhandler(ciphers.IntegrityError)
def integrity_failed(_e):
    return err("Integrity check failed (data corrupted or modified)", 500)


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return err("Token tidak ada", 401)
        token_hash = hashlib.sha256(header[7:].encode()).hexdigest()
        row = db.get_db().execute(
            "SELECT user_id FROM sessions WHERE token_hash=? AND expires_at>?",
            (token_hash, iso(now())),
        ).fetchone()
        if not row:
            return err("Sesi tidak valid atau sudah habis", 401)
        g.user_id, g.token_hash = row["user_id"], token_hash
        return fn(*args, **kwargs)

    return wrapper


def validate_registration(form, files):
    e = {}
    d = {k: form.get(k, "").strip() for k in
         ("full_name", "nik", "email", "phone", "date_of_birth", "address")}

    if len(d["full_name"]) < 3:
        e["full_name"] = "Minimal 3 karakter"
    if not re.fullmatch(r"\d{16}", d["nik"]):
        e["nik"] = "NIK harus 16 digit angka"
    if not EMAIL_RE.match(d["email"]):
        e["email"] = "Format email tidak valid"
    if not PHONE_RE.match(d["phone"]):
        e["phone"] = "Nomor HP Indonesia tidak valid (contoh 08123456789)"
    if len(d["address"]) < 10:
        e["address"] = "Alamat terlalu pendek"
    try:
        dob = date.fromisoformat(d["date_of_birth"])
        t = date.today()
        age = t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))
        if age < 17:
            e["date_of_birth"] = "Usia minimal 17 tahun"
    except ValueError:
        e["date_of_birth"] = "Format harus YYYY-MM-DD"

    password = form.get("password", "")
    if len(password) < 8:
        e["password"] = "Minimal 8 karakter"
    if form.get("consent_pdp", "").lower() not in ("true", "1", "on", "yes"):
        e["consent_pdp"] = "Persetujuan pemrosesan data pribadi wajib"

    uploads = {}
    for kind, exts in ALLOWED_FILES.items():
        f = files.get(kind)
        if not f or not f.filename:
            e[kind] = "File wajib diunggah"
            continue
        ext = Path(f.filename).suffix.lower()
        if ext not in exts:
            e[kind] = f"Ekstensi harus salah satu dari {sorted(exts)}"
            continue
        data = f.read()
        if not data:
            e[kind] = "File kosong"
            continue
        uploads[kind] = (Path(f.filename).name, data)
    return d, password, uploads, e


def new_account_number(conn):
    while True:
        number = "88" + "".join(str(secrets.randbelow(10)) for _ in range(10))
        if not conn.execute("SELECT 1 FROM users WHERE account_number=?", (number,)).fetchone():
            return number


# ---------- routes ----------
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/lumio")
def lumio():
    return render_template("lumio.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/register")
def register():
    """multipart/form-data: data pribadi + 3 file (ktp, supporting_doc, selfie_video)."""
    d, password, uploads, errors = validate_registration(request.form, request.files)
    if errors:
        return err("Validasi gagal", 422, fields=errors)

    conn = db.get_db()
    email_h, nik_h = lookup_hash(d["email"].lower()), lookup_hash(d["nik"])
    if conn.execute("SELECT 1 FROM users WHERE email_lookup=? OR nik_lookup=?",
                    (email_h, nik_h)).fetchone():
        return err("Email atau NIK sudah terdaftar", 409)

    written = []
    try:
        ts = iso(now())
        cur = conn.execute(
            "INSERT INTO users (email_lookup, nik_lookup, password_hash, profile, cipher,"
            " account_number, consent_at, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (email_h, nik_h, generate_password_hash(password), b"", hooks.cipher_for("profile"),
             new_account_number(conn), ts, ts),
        )
        uid = cur.lastrowid
        profile = json.dumps({**d, "email": d["email"].lower()}).encode()
        conn.execute("UPDATE users SET profile=? WHERE id=?",
                     (hooks.protect(profile, user_id=uid, purpose="profile"), uid))

        user_dir = STORAGE_DIR / str(uid)
        user_dir.mkdir(parents=True, exist_ok=True)
        for kind, (name, data) in uploads.items():
            path = user_dir / f"{secrets.token_hex(16)}.bin"
            path.write_bytes(hooks.protect(data, user_id=uid, purpose=kind))
            written.append(path)
            conn.execute(
                "INSERT INTO documents (user_id, kind, original_name, mime, path, size,"
                " sha256, cipher, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (uid, kind, name, mimetypes.guess_type(name)[0] or "application/octet-stream",
                 str(path), len(data), hashlib.sha256(data).hexdigest(),
                 hooks.cipher_for(kind), ts),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        for p in written:
            p.unlink(missing_ok=True)
        raise

    account = conn.execute("SELECT account_number FROM users WHERE id=?", (uid,)).fetchone()
    return jsonify({"message": "Pendaftaran berhasil",
                    "account_number": account["account_number"]}), 201


@app.post("/api/login")
def login():
    body = request.get_json(silent=True) or {}
    email, password = str(body.get("email", "")).lower(), str(body.get("password", ""))
    conn = db.get_db()
    user = conn.execute("SELECT id, password_hash FROM users WHERE email_lookup=?",
                        (lookup_hash(email),)).fetchone()
    if not user or not check_password_hash(user["password_hash"], password):
        return err("Email atau password salah", 401)

    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?,?,?)",
                 (hashlib.sha256(token.encode()).hexdigest(), user["id"],
                  iso(now() + timedelta(hours=SESSION_HOURS))))
    conn.commit()
    return jsonify({"token": token, "expires_in_hours": SESSION_HOURS})


@app.post("/api/logout")
@require_auth
def logout():
    conn = db.get_db()
    conn.execute("DELETE FROM sessions WHERE token_hash=?", (g.token_hash,))
    conn.commit()
    return jsonify({"message": "Logout berhasil"})


@app.get("/api/me")
@require_auth
def me():
    conn = db.get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (g.user_id,)).fetchone()
    profile = json.loads(hooks.unprotect(u["profile"], user_id=u["id"], purpose="profile"))
    docs = conn.execute("SELECT kind, original_name, mime, size, created_at "
                        "FROM documents WHERE user_id=?", (g.user_id,)).fetchall()
    return jsonify({
        "profile": profile,
        "account": {"number": u["account_number"], "balance": u["balance"]},
        "consent_at": u["consent_at"],
        "documents": [dict(r) for r in docs],
    })


@app.get("/api/me/documents/<kind>")
@require_auth
def download_document(kind):
    # Query selalu dibatasi user_id dari sesi: user hanya bisa mengambil file miliknya.
    row = db.get_db().execute("SELECT * FROM documents WHERE user_id=? AND kind=?",
                              (g.user_id, kind)).fetchone()
    if not row:
        return err("Dokumen tidak ditemukan", 404)
    data = hooks.unprotect(Path(row["path"]).read_bytes(), user_id=g.user_id, purpose=kind)
    if hashlib.sha256(data).hexdigest() != row["sha256"]:
        return err("Integritas file gagal diverifikasi", 500)
    return send_file(io.BytesIO(data), mimetype=row["mime"],
                     as_attachment=True, download_name=row["original_name"])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
