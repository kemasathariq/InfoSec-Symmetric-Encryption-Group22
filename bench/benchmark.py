"""
Speed test for AES-GCM, DES-CTR+HMAC and RC4+HMAC, using ciphers.encrypt/decrypt.
Tests 4 file sizes with random and repeated data. Every run checks the data comes back the same.
Method: docs/CRYPTO_DESIGN.md section 6.

    python bench/benchmark.py [--reps 30] [--out bench/results]
"""
import argparse
import csv
import gc
import hashlib
import os
import platform
import random
import statistics as st
import sys
import time
import tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "BE"))
os.environ.setdefault("MASTER_KEY", "benchmark-key")
import ciphers  # noqa: E402

OBJECTS = [("profile_1KB", 1_000), ("ktp_500KB", 500_000), ("office_doc_2MB", 2_000_000),
           ("selfie_video_20MB", 20_000_000)]
NAMES = ["aes", "des", "rc4", "aes+des+rc4"]  # last one = layered


def make(kind, n):
    if kind == "random":
        return os.urandom(n)
    unit = b"Salary slip Budi Santoso, PT Contoh Maju, Rp 8.500.000. "
    return (unit * (n // len(unit) + 1))[:n]


def ms(ns):
    return ns / 1e6


def summarize(xs):
    xs = sorted(xs)
    q = st.quantiles(xs, n=4) if len(xs) >= 4 else [xs[0], st.median(xs), xs[-1]]
    return st.median(xs), q[2] - q[0], st.stdev(xs) if len(xs) > 1 else 0.0


def timing(reps):
    rows = []
    for kind in ("random", "repetitive"):
        for label, n in OBJECTS:
            data = make(kind, n)
            digest = hashlib.sha256(data).digest()
            enc = {c: [] for c in NAMES}
            dec = {c: [] for c in NAMES}
            blobs = {}
            for rep in range(-3, reps):  # first 3 runs are warm-up, discarded
                order = NAMES[:]
                random.shuffle(order)
                for c in order:
                    gc.collect()
                    t = time.perf_counter_ns()
                    blob = ciphers.encrypt(c, data, user_id=1, purpose="ktp")
                    t_enc = time.perf_counter_ns() - t
                    t = time.perf_counter_ns()
                    out = ciphers.decrypt(blob, user_id=1, purpose="ktp")
                    t_dec = time.perf_counter_ns() - t
                    assert hashlib.sha256(out).digest() == digest, f"round trip failed for {c}"
                    if rep >= 0:
                        enc[c].append(ms(t_enc)); dec[c].append(ms(t_dec))
                    blobs[c] = len(blob)
            for c in NAMES:
                for op, xs in (("encrypt", enc[c]), ("decrypt", dec[c])):
                    med, iqr, sd = summarize(xs)
                    rows.append(dict(content=kind, object=label, size_bytes=n, cipher=c, op=op,
                                     reps=reps, median_ms=med, iqr_ms=iqr, stdev_ms=sd,
                                     throughput_MBps=(n / 1e6) / (med / 1e3),
                                     blob_bytes=blobs[c], overhead_bytes=blobs[c] - n))
            print(f"timed {kind}/{label}", flush=True)
    return rows


def hkdf_cost(reps):
    xs = []
    for _ in range(reps * 10):
        t = time.perf_counter_ns()
        ciphers._derive("aes", os.urandom(16), 1, "ktp", 32)
        xs.append(ms(time.perf_counter_ns() - t))
    return st.median(xs)


def memory():
    out = {}
    for label, n in OBJECTS:
        data = os.urandom(n)
        for c in NAMES:
            gc.collect()
            tracemalloc.start()
            base = tracemalloc.get_traced_memory()[0]
            blob = ciphers.encrypt(c, data, user_id=1, purpose="ktp")
            ciphers.decrypt(blob, user_id=1, purpose="ktp")
            peak = tracemalloc.get_traced_memory()[1] - base
            tracemalloc.stop()
            out[(label, c)] = peak / max(n, 1)
    return out


def rc4_bias(trials=200_000):
    """Chance that the 2nd output byte is 0. Ideal is 1/256, plain RC4 is about 2/256."""
    from Crypto.Cipher import ARC4
    res = {}
    for drop in (0, ciphers.RC4_DROP):
        hits = 0
        for _ in range(trials):
            ks = ARC4.new(os.urandom(16), drop=drop).encrypt(b"\0\0")
            hits += ks[1] == 0
        res[drop] = hits / trials * 256  # kelipatan dari probabilitas ideal
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--out", default=str(Path(__file__).parent / "results"))
    a = ap.parse_args()
    out = Path(a.out)

    env = (f"Python {platform.python_version()}, {platform.system()} {platform.machine()}, "
           f"{platform.processor() or 'cpu n/a'}, pycryptodome")
    rows = timing(a.reps)
    hk = hkdf_cost(a.reps)
    mem = memory()
    bias = rc4_bias()

    with open(f"{out}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    def get(content, obj, c, op):
        return next(r for r in rows if r["content"] == content and r["object"] == obj
                    and r["cipher"] == c and r["op"] == op)

    L = [f"# Benchmark results\n", f"Environment: {env}. Runs: {a.reps} (+3 warm-up). Time = median [IQR] in ms.\n"]
    L.append("## Time per object (random content)\n")
    L.append("| Object | Cipher | Encrypt ms | Decrypt ms | MB/s (enc) | MB/s (dec) | Overhead B | Peak mem (x size) |")
    L.append("|---|---|---|---|---|---|---|---|")
    for label, _ in OBJECTS:
        for c in NAMES:
            e, d = get("random", label, c, "encrypt"), get("random", label, c, "decrypt")
            L.append(f"| {label} | {c.upper()} | {e['median_ms']:.2f} [{e['iqr_ms']:.2f}] | "
                     f"{d['median_ms']:.2f} [{d['iqr_ms']:.2f}] | {e['throughput_MBps']:.0f} | "
                     f"{d['throughput_MBps']:.0f} | {e['overhead_bytes']} | {mem[(label, c)]:.1f} |")
    L.append("\n## One registration (profile + KTP + doc + video), random content\n")
    L.append("| Cipher | Total encrypt ms | Total decrypt ms | vs AES (enc) |")
    L.append("|---|---|---|---|")
    tot = {c: (sum(get("random", o, c, "encrypt")["median_ms"] for o, _ in OBJECTS),
               sum(get("random", o, c, "decrypt")["median_ms"] for o, _ in OBJECTS)) for c in NAMES}
    for c in NAMES:
        L.append(f"| {c.upper()} | {tot[c][0]:.0f} | {tot[c][1]:.0f} | {tot[c][0] / tot['aes'][0]:.2f}x |")
    # Side by side: the three ways to protect one registration.
    kinds = [o for o, _ in OBJECTS]
    per_type = dict(zip(kinds, ["aes", "des", "rc4", "aes"]))
    plans = [("All AES", dict.fromkeys(kinds, "aes"), "AES"),
             ("One cipher per data type (default)", per_type, "DES (the KTP)"),
             ("Layered AES+DES+RC4 on everything", dict.fromkeys(kinds, "aes+des+rc4"),
              "all three, attacker must break each layer")]
    L.append("\n## Side by side: one registration (profile + KTP + doc + video), random content\n")
    L.append("| Setup | Encrypt ms | Decrypt ms | vs all-AES | Extra bytes | Weakest protection of any item |")
    L.append("|---|---|---|---|---|---|")
    base = sum(get("random", o, "aes", "encrypt")["median_ms"] for o in kinds)
    for title, plan, weakest in plans:
        e = sum(get("random", o, plan[o], "encrypt")["median_ms"] for o in kinds)
        d = sum(get("random", o, plan[o], "decrypt")["median_ms"] for o in kinds)
        extra = sum(get("random", o, plan[o], "encrypt")["overhead_bytes"] for o in kinds)
        L.append(f"| {title} | {e:.0f} | {d:.0f} | {e / base:.1f}x | {extra} | {weakest} |")
    L.append("\n## Random vs repetitive content (selfie_video_20MB, encrypt, median ms)\n")
    L.append("| Cipher | Random | Repetitive | Difference |")
    L.append("|---|---|---|---|")
    for c in NAMES:
        r, p = get("random", "selfie_video_20MB", c, "encrypt")["median_ms"], get("repetitive", "selfie_video_20MB", c, "encrypt")["median_ms"]
        L.append(f"| {c.upper()} | {r:.1f} | {p:.1f} | {abs(r - p) / r * 100:.1f}% |")
    L.append(f"\nHKDF key derivation per object: median {hk * 1000:.0f} us, independent of size.\n")
    L.append("## RC4 keystream bias (2nd byte = 0, multiple of the ideal 1/256)\n")
    L.append(f"- No drop: {bias[0]:.2f}x (ideal 1.00x, theory ~2x)")
    L.append(f"- Drop {ciphers.RC4_DROP}: {bias[ciphers.RC4_DROP]:.2f}x\n")
    Path(f"{out}.md").write_text("\n".join(L))
    print("\n".join(L))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
        for i, op in enumerate(("encrypt", "decrypt")):
            for j, c in enumerate(NAMES):
                ax[i].bar([k + j * 0.2 for k in range(len(OBJECTS))],
                          [get("random", o, c, op)["throughput_MBps"] for o, _ in OBJECTS],
                          0.2, label=c.upper())
            ax[i].set_xticks([k + 0.3 for k in range(len(OBJECTS))])
            ax[i].set_xticklabels([o.split("_")[0] if o != "office_doc_2MB" else "doc" for o, _ in OBJECTS])
            ax[i].set_yscale("log"); ax[i].set_ylabel("MB/s (log)"); ax[i].set_title(op)
        ax[0].legend()
        fig.tight_layout(); fig.savefig(f"{out}.png", dpi=150)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
