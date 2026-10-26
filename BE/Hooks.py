"""
Every private value goes through protect() before saving and unprotect() after reading.
Each data type has its own cipher (see POLICY). Reasons: docs/CRYPTO_DESIGN.md section 4.

Env options:
  CIPHER=aes|des|rc4          use one cipher for everything
  CIPHER_POLICY=ktp=aes,...   change the cipher of single data types
"""
import os

import ciphers

PURPOSES = ("profile", "ktp", "supporting_doc", "selfie_video")

POLICY = {
    "profile": "aes",
    "selfie_video": "aes",
    "supporting_doc": "rc4",
    "ktp": "des",
}


def _load_policy() -> dict:
    policy = dict(POLICY)
    for item in filter(None, os.environ.get("CIPHER_POLICY", "").split(",")):
        purpose, _, name = item.partition("=")
        policy[purpose.strip()] = name.strip().lower()
    forced = os.environ.get("CIPHER", "").lower()
    if forced:
        policy = dict.fromkeys(PURPOSES, forced)
    for purpose, name in policy.items():
        if purpose not in PURPOSES or name not in ciphers.CIPHERS:
            raise RuntimeError(f"Bad cipher policy {purpose}={name}; "
                               f"purposes {PURPOSES}, ciphers {sorted(ciphers.CIPHERS)}")
    return policy


ACTIVE_POLICY = _load_policy()


def cipher_for(purpose: str) -> str:
    return ACTIVE_POLICY[purpose]


def protect(data: bytes, *, user_id: int, purpose: str) -> bytes:
    return ciphers.encrypt(cipher_for(purpose), data, user_id=user_id, purpose=purpose)


def unprotect(data: bytes, *, user_id: int, purpose: str) -> bytes:
    return ciphers.decrypt(data, user_id=user_id, purpose=purpose)
