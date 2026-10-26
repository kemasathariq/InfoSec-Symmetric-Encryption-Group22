import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "BE"))
os.environ["MASTER_KEY"] = "test-master-key"
import ciphers  # noqa: E402

SIZES = [0, 1, 7, 8, 9, 15, 16, 17, 1000, 100_000]


class RoundTrip(unittest.TestCase):
    def test_roundtrip_all_ciphers_and_sizes(self):
        for name in ciphers.CIPHERS:
            for n in SIZES:
                data = os.urandom(n)
                blob = ciphers.encrypt(name, data, user_id=1, purpose="ktp")
                self.assertEqual(ciphers.decrypt(blob, user_id=1, purpose="ktp"), data, (name, n))
                self.assertEqual(len(blob), n + ciphers.overhead(name, n), (name, n))

    def test_no_plaintext_in_blob(self):
        marker = b"NIK=3578012345670001 Budi Santoso " * 20
        for name in ciphers.CIPHERS:
            blob = ciphers.encrypt(name, marker, user_id=1, purpose="profile")
            self.assertNotIn(b"3578012345670001", blob)
            self.assertNotIn(b"Budi", blob)

    def test_same_plaintext_gives_different_ciphertext(self):
        # Same input twice must give different output.
        data = b"A" * 64
        for name in ciphers.CIPHERS:
            self.assertNotEqual(ciphers.encrypt(name, data, user_id=1, purpose="ktp"),
                                ciphers.encrypt(name, data, user_id=1, purpose="ktp"))

    def test_repeated_blocks_not_visible(self):
        # ECB check: repeated blocks must not repeat in the ciphertext.
        data = b"B" * 8 * 16
        for name, bs in (("aes", 16), ("des", 8), ("rc4", 8)):
            blob = ciphers.encrypt(name, data, user_id=1, purpose="ktp")
            ct = blob[ciphers.HEADER_FIXED + ciphers.CIPHERS[name].iv_len:-ciphers.CIPHERS[name].tag_len]
            blocks = [ct[i:i + bs] for i in range(0, len(ct), bs)]
            self.assertEqual(len(blocks), len(set(blocks)))


class Tamper(unittest.TestCase):
    def test_every_single_bit_flip_position_rejected(self):
        data = os.urandom(200)
        for name in ciphers.CIPHERS:
            blob = ciphers.encrypt(name, data, user_id=1, purpose="ktp")
            for i in range(len(blob)):
                bad = bytearray(blob)
                bad[i] ^= 0x01
                with self.assertRaises(ciphers.IntegrityError, msg=(name, i)):
                    ciphers.decrypt(bytes(bad), user_id=1, purpose="ktp")

    def test_truncated_and_garbage(self):
        for blob in (b"", b"x", os.urandom(64), ciphers.encrypt("aes", b"hi", user_id=1, purpose="ktp")[:-1]):
            with self.assertRaises(ciphers.IntegrityError):
                ciphers.decrypt(blob, user_id=1, purpose="ktp")

    def test_blob_bound_to_user_and_purpose(self):
        for name in ciphers.CIPHERS:
            blob = ciphers.encrypt(name, b"secret", user_id=1, purpose="ktp")
            with self.assertRaises(ciphers.IntegrityError):
                ciphers.decrypt(blob, user_id=2, purpose="ktp")
            with self.assertRaises(ciphers.IntegrityError):
                ciphers.decrypt(blob, user_id=1, purpose="selfie_video")

    def test_wrong_master_key(self):
        blob = ciphers.encrypt("aes", b"secret", user_id=1, purpose="ktp")
        os.environ["MASTER_KEY"] = "another-key"
        try:
            with self.assertRaises(ciphers.IntegrityError):
                ciphers.decrypt(blob, user_id=1, purpose="ktp")
        finally:
            os.environ["MASTER_KEY"] = "test-master-key"


if __name__ == "__main__":
    unittest.main()
