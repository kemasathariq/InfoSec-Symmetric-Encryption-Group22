"""
Speed test of different modes on a 20 MB file (selfie video size).
All variants are authenticated: GCM, or CTR/CBC/OFB + HMAC.

    python bench/mode_comparison.py [--reps 30]
"""
import argparse
import hashlib
import hmac
import os
import random
import statistics as st
import time
from pathlib import Path

from Crypto.Cipher import AES, DES
from Crypto.Util import Counter
from Crypto.Util.Padding import pad

N = 20_000_000
KM = os.urandom(32)  # HMAC key


def mac(ct):
    return hmac.new(KM, ct, hashlib.sha256).digest()


def aes_gcm(d):
    c = AES.new(os.urandom(32), AES.MODE_GCM, nonce=os.urandom(12)); c.encrypt_and_digest(d)

def aes_cbc(d):
    mac(AES.new(os.urandom(32), AES.MODE_CBC, iv=os.urandom(16)).encrypt(pad(d, 16)))

def aes_ctr(d):
    mac(AES.new(os.urandom(32), AES.MODE_CTR, nonce=os.urandom(8)).encrypt(d))

def des_cbc(d):
    mac(DES.new(os.urandom(8), DES.MODE_CBC, iv=os.urandom(8)).encrypt(pad(d, 8)))

def des_ctr(d):
    mac(DES.new(os.urandom(8), DES.MODE_CTR, nonce=os.urandom(4)).encrypt(d))

def des_ofb(d):
    mac(DES.new(os.urandom(8), DES.MODE_OFB, iv=os.urandom(8)).encrypt(d))

def hmac_only(d):
    mac(d)


VARIANTS = [("AES-GCM", aes_gcm), ("AES-CBC+HMAC", aes_cbc), ("AES-CTR+HMAC", aes_ctr),
            ("DES-CBC+HMAC", des_cbc), ("DES-CTR+HMAC", des_ctr), ("DES-OFB+HMAC", des_ofb),
            ("HMAC-SHA256 only", hmac_only)]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=30)
    reps = ap.parse_args().reps
    data = os.urandom(N)
    res = {n: [] for n, _ in VARIANTS}
    for rep in range(-3, reps):
        random.shuffle(VARIANTS)
        for n, f in VARIANTS:
            t = time.perf_counter(); f(data); dt = time.perf_counter() - t
            if rep >= 0:
                res[n].append(dt * 1000)
    lines = ["# Mode comparison (20 MB encryption, median of %d runs)\n" % reps,
             "| Variant | Median ms | Stdev ms | MB/s |", "|---|---|---|---|"]
    for n in sorted(res, key=lambda k: st.median(res[k])):
        m = st.median(res[n])
        lines.append(f"| {n} | {m:.1f} | {st.stdev(res[n]):.1f} | {N / 1e6 / (m / 1e3):.0f} |")
    out = "\n".join(lines)
    Path(__file__).with_name("modes.md").write_text(out + "\n")
    print(out)


if __name__ == "__main__":
    main()
