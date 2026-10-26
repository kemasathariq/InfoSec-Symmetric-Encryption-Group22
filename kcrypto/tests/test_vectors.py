"""Known-answer tests: prove the primitives we build on behave per the standards.

(ECB never appears in the product code. DES is checked via CBC with a zero IV,
which equals a single ECB block.)
"""
from binascii import unhexlify as h

from Crypto.Cipher import AES, ARC4, DES
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import HKDF


def test_aes256_gcm_nist_case13_empty():
    c = AES.new(bytes(32), AES.MODE_GCM, nonce=bytes(12), mac_len=16)
    ct, tag = c.encrypt_and_digest(b"")
    assert ct == b""
    assert tag == h("530f8afbc74536b9a963b4f1c4cb738b")


def test_aes256_gcm_nist_case14_one_block():
    c = AES.new(bytes(32), AES.MODE_GCM, nonce=bytes(12), mac_len=16)
    ct, tag = c.encrypt_and_digest(bytes(16))
    assert ct == h("cea7403d4d606b6e074ec5d3baf39d18")
    assert tag == h("d0d1c8a799996bf0265b98b5d48ab919")


def test_des_classic_vector():
    # key 133457799BBCDFF1, pt 0123456789ABCDEF -> 85E813540F0AB405
    c = DES.new(h("133457799BBCDFF1"), DES.MODE_CBC, iv=bytes(8))
    assert c.encrypt(h("0123456789ABCDEF")) == h("85E813540F0AB405")


def test_rc4_known_vectors():
    assert ARC4.new(b"Key").encrypt(b"Plaintext") == h("BBF316E8D940AF0AD3")
    assert ARC4.new(b"Wiki").encrypt(b"pedia") == h("1021BF0420")
    assert ARC4.new(b"Secret").encrypt(b"Attack at dawn") == h("45A01F645FC35B383552544B9BF5")


def test_hkdf_rfc5869_case1():
    okm = HKDF(
        h("0b" * 22), 42, h("000102030405060708090a0b0c"), SHA256, 1,
        h("f0f1f2f3f4f5f6f7f8f9"),
    )
    assert okm == h(
        "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865"
    )
