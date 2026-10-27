"""
Encrypt and decrypt data with AES, DES or RC4.

Every encrypted blob looks like this:
    magic | cipher_id | salt | iv/nonce | ciphertext | tag
A layered blob (e.g. "aes+des+rc4") wraps one blob inside the next:
    magic_layered | layer_count | outer blob( ... inner blob(data) )

Each object gets its own key, made from MASTER_KEY and a random salt.
The tag also covers user_id and purpose, so a blob copied to another
user or document type fails to decrypt.
"""
import hmac
import hashlib
import os

from Crypto.Cipher import AES, ARC4, DES
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

MAGIC = b"\xc5\x01"
MAGIC_LAYERED = b"\xc5\x02"  # blob made of several ciphers on top of each other
MAX_LAYERS = 8
SALT_LEN = 16
HEADER_FIXED = len(MAGIC) + 1 + SALT_LEN

# The first RC4 output bytes are biased (Stallings 8.5), so we skip them.
RC4_DROP = 3072


class IntegrityError(Exception):
    """The tag does not match: data was changed or belongs to someone else."""


def _master_key() -> bytes:
    raw = os.environ.get("MASTER_KEY", "").strip()
    if not raw:
        if os.environ.get("APP_ENV") == "production":
            raise RuntimeError("MASTER_KEY is required when APP_ENV=production")
        raw = "dev-only-master-key-change-me"  # only for tests and benchmarks
    return hashlib.sha256(raw.encode()).digest()


def _derive(cipher: str, salt: bytes, user_id: int, purpose: str, n: int) -> bytes:
    info = f"{cipher}|{user_id}|{purpose}".encode()
    return HKDF(_master_key(), n, salt, SHA256, context=info)


def _aad(header: bytes, user_id: int, purpose: str) -> bytes:
    return header + f"|{user_id}|{purpose}".encode()


# ---------- AES-256-GCM ----------
class AesGcm:
    id, name, iv_len, tag_len = 1, "aes", 12, 16

    @staticmethod
    def encrypt(key_material: bytes, iv: bytes, aad: bytes, data: bytes):
        c = AES.new(key_material, AES.MODE_GCM, nonce=iv)
        c.update(aad)
        ct, tag = c.encrypt_and_digest(data)
        return ct, tag

    @staticmethod
    def decrypt(key_material: bytes, iv: bytes, aad: bytes, ct: bytes, tag: bytes):
        c = AES.new(key_material, AES.MODE_GCM, nonce=iv)
        c.update(aad)
        try:
            return c.decrypt_and_verify(ct, tag)
        except ValueError as e:
            raise IntegrityError("GCM tag mismatch") from e

    key_len = 32  # AES-256


# ---------- DES-CTR + HMAC-SHA256 (encrypt-then-MAC) ----------
# CTR is the fastest DES mode we tested (bench/modes.md) and needs no padding.
# Each object has its own key, so the nonce is never reused.
class DesCtr:
    id, name, iv_len, tag_len = 2, "des", 4, 32  # 4-byte nonce + 4-byte counter = 64-bit block
    key_len = 8 + 32  # 8-byte DES key + 32-byte HMAC key

    @staticmethod
    def encrypt(key_material, iv, aad, data):
        k_enc, k_mac = key_material[:8], key_material[8:]
        ct = DES.new(k_enc, DES.MODE_CTR, nonce=iv).encrypt(data)
        return ct, hmac.new(k_mac, aad + ct, hashlib.sha256).digest()

    @staticmethod
    def decrypt(key_material, iv, aad, ct, tag):
        k_enc, k_mac = key_material[:8], key_material[8:]
        expect = hmac.new(k_mac, aad + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(expect, tag):
            raise IntegrityError("HMAC mismatch")
        return DES.new(k_enc, DES.MODE_CTR, nonce=iv).decrypt(ct)


# ---------- RC4-drop + HMAC-SHA256 (encrypt-then-MAC) ----------
class Rc4Drop:
    id, name, iv_len, tag_len = 3, "rc4", 0, 32  # RC4 has no IV; the per-object key keeps the output unique
    key_len = 16 + 32

    @staticmethod
    def encrypt(key_material, iv, aad, data):
        k_enc, k_mac = key_material[:16], key_material[16:]
        ct = ARC4.new(k_enc, drop=RC4_DROP).encrypt(data)
        return ct, hmac.new(k_mac, aad + ct, hashlib.sha256).digest()

    @staticmethod
    def decrypt(key_material, iv, aad, ct, tag):
        k_enc, k_mac = key_material[:16], key_material[16:]
        expect = hmac.new(k_mac, aad + ct, hashlib.sha256).digest()
        if not hmac.compare_digest(expect, tag):
            raise IntegrityError("HMAC mismatch")
        return ARC4.new(k_enc, drop=RC4_DROP).decrypt(ct)


CIPHERS = {c.name: c for c in (AesGcm, DesCtr, Rc4Drop)}
_BY_ID = {c.id: c for c in CIPHERS.values()}


def _encrypt_one(cipher: str, data: bytes, user_id: int, purpose: str) -> bytes:
    c = CIPHERS[cipher]
    salt, iv = get_random_bytes(SALT_LEN), get_random_bytes(c.iv_len)
    header = MAGIC + bytes([c.id]) + salt + iv
    key = _derive(cipher, salt, user_id, purpose, c.key_len)
    ct, tag = c.encrypt(key, iv, _aad(header, user_id, purpose), data)
    return header + ct + tag


def _decrypt_one(blob: bytes, user_id: int, purpose: str) -> bytes:
    if len(blob) < HEADER_FIXED + 1 or blob[:2] != MAGIC or blob[2] not in _BY_ID:
        raise IntegrityError("Unknown blob format")
    c = _BY_ID[blob[2]]
    if len(blob) < HEADER_FIXED + c.iv_len + c.tag_len:
        raise IntegrityError("Blob too short")
    hdr_len = HEADER_FIXED + c.iv_len
    header, ct, tag = blob[:hdr_len], blob[hdr_len:-c.tag_len], blob[-c.tag_len:]
    salt, iv = header[3:3 + SALT_LEN], header[3 + SALT_LEN:]
    key = _derive(c.name, salt, user_id, purpose, c.key_len)
    return c.decrypt(key, iv, _aad(header, user_id, purpose), ct, tag)


def encrypt(cipher: str, data: bytes, *, user_id: int, purpose: str) -> bytes:
    """cipher is one name ("aes") or layers joined by "+" ("aes+des+rc4", first = innermost)."""
    if "+" not in cipher:
        return _encrypt_one(cipher, data, user_id, purpose)
    names = cipher.split("+")
    blob = data
    for i, name in enumerate(names):
        blob = _encrypt_one(name, blob, user_id, f"{purpose}|layer{i}of{len(names)}")
    return MAGIC_LAYERED + bytes([len(names)]) + blob


def decrypt(blob: bytes, *, user_id: int, purpose: str) -> bytes:
    if blob[:2] != MAGIC_LAYERED:
        return _decrypt_one(blob, user_id, purpose)
    if len(blob) < 4 or not 1 <= blob[2] <= MAX_LAYERS:
        raise IntegrityError("Bad layer count")
    n, data = blob[2], blob[3:]
    # Each layer's label contains its position and the total, so a changed count fails here.
    for i in reversed(range(n)):
        data = _decrypt_one(data, user_id, f"{purpose}|layer{i}of{n}")
    return data


def overhead(cipher: str, plain_len: int) -> int:
    """Extra bytes added to the data (headers + tags)."""
    if "+" in cipher:
        return len(MAGIC_LAYERED) + 1 + sum(overhead(n, 0) for n in cipher.split("+"))
    c = CIPHERS[cipher]
    return HEADER_FIXED + c.iv_len + c.tag_len
