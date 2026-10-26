import io
import os
import pathlib

import pytest

from kcrypto import ALGOS, decrypt_bytes, encrypt_bytes, new_key
from kcrypto.api import decrypt_stream, encrypt_all, encrypt_stream, verify_copies
from kcrypto.format import HEADER_LEN

CS = 4096
SIZES = [0, 1, 7, 8, 15, 16, CS - 1, CS, CS + 1, 10_000, 3 * CS, 3 * CS + 1]


@pytest.mark.parametrize("algo", ALGOS)
@pytest.mark.parametrize("size", SIZES)
def test_roundtrip_edge_sizes(algo, size):
    dek, data = new_key(), os.urandom(size)
    blob = encrypt_bytes(data, dek, algo, chunk_size=CS)
    assert decrypt_bytes(blob, dek, algo) == data


@pytest.mark.parametrize("algo", ALGOS)
def test_roundtrip_default_chunk_multi_mib(algo):
    dek, data = new_key(), os.urandom(2_500_000)  # 3 chunks of 1 MiB
    assert decrypt_bytes(encrypt_bytes(data, dek, algo), dek, algo) == data


@pytest.mark.parametrize("algo", ALGOS)
def test_same_plaintext_gives_different_ciphertext(algo):
    dek, data = new_key(), b"A" * 5000
    assert encrypt_bytes(data, dek, algo) != encrypt_bytes(data, dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_no_plaintext_leak_in_repeating_blocks(algo):
    """A crude anti-ECB check: identical plaintext blocks must not give identical ciphertext blocks."""
    dek = new_key()
    blob = encrypt_bytes(b"\x00" * 4096, dek, algo, chunk_size=4096)[HEADER_LEN:]
    blocks = [blob[i : i + 16] for i in range(0, 2048, 16)]
    assert len(set(blocks)) == len(blocks)


@pytest.mark.parametrize("algo", ALGOS)
def test_meta_sizes_and_hashes(algo):
    import hashlib

    dek, data = new_key(), os.urandom(9000)
    out = io.BytesIO()
    m = encrypt_stream(io.BytesIO(data), out, dek, algo, chunk_size=CS)
    assert m.pt_size == len(data) and m.ct_size == len(out.getvalue())
    assert m.pt_sha256 == hashlib.sha256(data).digest()
    assert m.ct_sha256 == hashlib.sha256(out.getvalue()).digest()
    out.seek(0)
    sink = io.BytesIO()
    m2 = decrypt_stream(out, sink, dek, algo)
    assert m2.pt_sha256 == m.pt_sha256 and sink.getvalue() == data


def test_encrypt_all_and_verify_copies(tmp_path):
    dek, data = new_key(), os.urandom(50_000)
    src = io.BytesIO(data)
    handles = {}

    def open_dst(a):
        handles[a] = open(tmp_path / f"{a}.enc", "wb")
        return handles[a]

    metas = encrypt_all(src, open_dst, dek, chunk_size=CS)
    for f in handles.values():
        f.close()
    assert set(metas) == set(ALGOS)
    assert len({m.pt_sha256 for m in metas.values()}) == 1

    rep = verify_copies(lambda a: open(tmp_path / f"{a}.enc", "rb"), dek)
    assert rep.ok and not rep.failed

    # corrupt only the DES copy -> report must flag exactly that one
    p = tmp_path / "des.enc"
    raw = bytearray(p.read_bytes())
    raw[HEADER_LEN + 20] ^= 1
    p.write_bytes(bytes(raw))
    rep = verify_copies(lambda a: open(tmp_path / f"{a}.enc", "rb"), dek)
    assert not rep.ok and rep.failed == ("des",)


def test_no_ecb_anywhere_in_source():
    root = pathlib.Path(__file__).resolve().parents[1]
    for py in root.rglob("*.py"):
        if "tests" in py.parts:
            continue
        assert "MODE_ECB" not in py.read_text(), f"ECB found in {py}"
