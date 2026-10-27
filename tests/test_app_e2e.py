"""
Full flow through Flask: register, login, download, for each cipher.
"""
from contextlib import closing
import hashlib
import importlib
import io
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

BE = str(Path(__file__).resolve().parents[1] / "BE")


def load_app(cipher, tmp):
    os.environ.update(MASTER_KEY="e2e", DB_PATH=f"{tmp}/t.db", STORAGE_DIR=f"{tmp}/st")
    if cipher:
        os.environ["CIPHER"] = cipher
    else:
        os.environ.pop("CIPHER", None)
    if BE not in sys.path:
        sys.path.insert(0, BE)
    for m in ("Hooks", "DB", "App"):
        sys.modules.pop(m, None)
    return importlib.import_module("App")


FORM = dict(full_name="Budi Santoso", nik="3578012345670001", email="budi@mail.com",
            phone="08123456789", date_of_birth="2000-05-01", address="Jl. Raya No. 1 Surabaya",
            password="rahasia123", consent_pdp="true")


class E2E(unittest.TestCase):
    def run_cipher(self, cipher):
        with tempfile.TemporaryDirectory() as tmp:
            app = load_app(cipher, tmp).app
            c = app.test_client()
            files = {"ktp": os.urandom(5000), "supporting_doc": os.urandom(30000),
                     "selfie_video": os.urandom(400000)}
            names = {"ktp": "ktp.jpg", "supporting_doc": "slip.pdf", "selfie_video": "v.mp4"}
            data = dict(FORM, **{k: (io.BytesIO(v), names[k]) for k, v in files.items()})
            r = c.post("/api/register", data=data, content_type="multipart/form-data")
            self.assertEqual(r.status_code, 201, r.json)
            tok = c.post("/api/login", json={"email": "budi@mail.com", "password": "rahasia123"}).json["token"]
            h = {"Authorization": f"Bearer {tok}"}
            me = c.get("/api/me", headers=h).json
            self.assertEqual(me["profile"]["nik"], FORM["nik"])
            for k, v in files.items():
                got = c.get(f"/api/me/documents/{k}", headers=h).data
                self.assertEqual(hashlib.sha256(got).digest(), hashlib.sha256(v).digest(), k)
            # no token means 401
            self.assertEqual(c.get("/api/me").status_code, 401)
            # nothing readable in DB or storage
            with closing(sqlite3.connect(f"{tmp}/t.db")) as conn:
                raw_db = conn.execute("SELECT profile FROM users").fetchone()[0]
            self.assertNotIn(b"3578012345670001", raw_db)
            self.assertNotIn(b"Budi", raw_db)
            for p in Path(f"{tmp}/st").rglob("*.bin"):
                for k, v in files.items():
                    self.assertNotIn(v[:64], p.read_bytes())
            # a damaged file gives an error, not wrong data
            p = next(Path(f"{tmp}/st").rglob("*.bin"))
            b = bytearray(p.read_bytes()); b[40] ^= 1; p.write_bytes(bytes(b))
            codes = {c.get(f"/api/me/documents/{k}", headers=h).status_code for k in files}
            self.assertIn(500, codes)

    def test_default_policy(self):
        # each data type uses its own cipher (check blob and DB column)
        import ciphers
        with tempfile.TemporaryDirectory() as tmp:
            mod = load_app(None, tmp)
            c = mod.app.test_client()
            files = {"ktp": (io.BytesIO(os.urandom(2000)), "k.jpg"),
                     "supporting_doc": (io.BytesIO(os.urandom(2000)), "s.pdf"),
                     "selfie_video": (io.BytesIO(os.urandom(2000)), "v.mp4")}
            r = c.post("/api/register", data=dict(FORM, **files), content_type="multipart/form-data")
            self.assertEqual(r.status_code, 201, r.json)
            with closing(sqlite3.connect(f"{tmp}/t.db")) as conn:
                expected = {"ktp": "des", "supporting_doc": "rc4", "selfie_video": "aes"}
                for kind, path, cipher in conn.execute("SELECT kind, path, cipher FROM documents"):
                    blob_id = Path(path).read_bytes()[2]
                    self.assertEqual(ciphers._BY_ID[blob_id].name, expected[kind], kind)
                    self.assertEqual(cipher, expected[kind], kind)
                profile_blob, cipher = conn.execute("SELECT profile, cipher FROM users").fetchone()
                self.assertEqual((ciphers._BY_ID[profile_blob[2]].name, cipher), ("aes", "aes"))

    def test_layered(self): self.run_cipher("layered")
    def test_aes(self): self.run_cipher("aes")
    def test_des(self): self.run_cipher("des")
    def test_rc4(self): self.run_cipher("rc4")


if __name__ == "__main__":
    unittest.main()
