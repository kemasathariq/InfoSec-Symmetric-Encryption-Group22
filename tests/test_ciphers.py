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


class Layered(unittest.TestCase):
    LAYERS = ["aes+des+rc4", "rc4+des+aes", "aes+rc4"]

    def test_roundtrip_and_size(self):
        for layers in self.LAYERS:
            for n in (0, 1, 17, 1000, 100_000):
                data = os.urandom(n)
                blob = ciphers.encrypt(layers, data, user_id=1, purpose="ktp")
                self.assertEqual(ciphers.decrypt(blob, user_id=1, purpose="ktp"), data, (layers, n))
                self.assertEqual(len(blob), n + ciphers.overhead(layers, n), (layers, n))

    def test_no_plaintext_and_random_each_time(self):
        data = b"NIK=3578012345670001 Budi Santoso " * 20
        a = ciphers.encrypt("aes+des+rc4", data, user_id=1, purpose="profile")
        b = ciphers.encrypt("aes+des+rc4", data, user_id=1, purpose="profile")
        self.assertNotEqual(a, b)
        self.assertNotIn(b"3578012345670001", a)

    def test_every_bit_flip_rejected(self):
        blob = ciphers.encrypt("aes+des+rc4", os.urandom(100), user_id=1, purpose="ktp")
        for i in range(len(blob)):
            bad = bytearray(blob)
            bad[i] ^= 0x01
            with self.assertRaises(ciphers.IntegrityError, msg=i):
                ciphers.decrypt(bytes(bad), user_id=1, purpose="ktp")

    def test_bound_to_user_and_purpose(self):
        blob = ciphers.encrypt("aes+des+rc4", b"secret", user_id=1, purpose="ktp")
        for uid, purpose in ((2, "ktp"), (1, "selfie_video")):
            with self.assertRaises(ciphers.IntegrityError):
                ciphers.decrypt(blob, user_id=uid, purpose=purpose)

    def test_changed_layer_count_is_detected(self):
        # Claiming 2 layers (or 1, or 4) on a 3-layer blob must fail, not return inner data.
        blob = ciphers.encrypt("aes+des+rc4", b"secret", user_id=1, purpose="ktp")
        for n in (1, 2, 4):
            forged = ciphers.MAGIC_LAYERED + bytes([n]) + blob[3:]
            with self.assertRaises(ciphers.IntegrityError, msg=n):
                ciphers.decrypt(forged, user_id=1, purpose="ktp")


if __name__ == "__main__":
    unittest.main()
