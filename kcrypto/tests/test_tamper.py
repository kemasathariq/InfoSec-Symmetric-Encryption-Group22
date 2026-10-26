"""Every kind of manipulation must raise IntegrityError - never return wrong data."""
import io
import os

import pytest

from kcrypto import ALGOS, IntegrityError, decrypt_bytes, encrypt_bytes, new_key
from kcrypto.format import HEADER_LEN
from kcrypto.suites import get_suite

CS = 64


def _make(algo, size=150):
    dek, data = new_key(), os.urandom(size)
    return dek, data, encrypt_bytes(data, dek, algo, chunk_size=CS)


@pytest.mark.parametrize("algo", ALGOS)
def test_flip_every_single_byte(algo):
    """Exhaustive: corrupting ANY byte (header, IV, ciphertext, tag/MAC) is detected."""
    dek, data, blob = _make(algo)
    for pos in range(len(blob)):
        bad = bytearray(blob)
        bad[pos] ^= 0x01
        with pytest.raises(IntegrityError):
            decrypt_bytes(bytes(bad), dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_flip_every_bit_of_header(algo):
    dek, data, blob = _make(algo)
    for pos in range(HEADER_LEN):
        for bit in range(8):
            bad = bytearray(blob)
            bad[pos] ^= 1 << bit
            with pytest.raises(IntegrityError):
                decrypt_bytes(bytes(bad), dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_truncation_at_every_length(algo):
    dek, data, blob = _make(algo)
    for n in range(len(blob)):
        with pytest.raises(IntegrityError):
            decrypt_bytes(blob[:n], dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_appended_data_rejected(algo):
    dek, data, blob = _make(algo)
    with pytest.raises(IntegrityError):
        decrypt_bytes(blob + b"\x00", dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_chunk_reorder_and_duplication_rejected(algo):
    dek, data, blob = _make(algo, size=CS * 4)  # 4 full chunks
    s = get_suite(algo)
    L = s.ct_len(CS)
    chunks = [blob[HEADER_LEN + i * L : HEADER_LEN + (i + 1) * L] for i in range(4)]
    head = blob[:HEADER_LEN]
    swapped = head + chunks[1] + chunks[0] + chunks[2] + chunks[3]
    dup = head + chunks[0] + chunks[0] + chunks[2] + chunks[3]
    dropped_mid = head + chunks[0] + chunks[1] + chunks[3] + chunks[3]
    for bad in (swapped, dup, dropped_mid):
        with pytest.raises(IntegrityError):
            decrypt_bytes(bad, dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_wrong_key_rejected(algo):
    dek, data, blob = _make(algo)
    with pytest.raises(IntegrityError):
        decrypt_bytes(blob, new_key(), algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_chunks_cannot_be_spliced_between_files(algo):
    dek = new_key()
    data = os.urandom(CS * 3)
    a = encrypt_bytes(data, dek, algo, chunk_size=CS)
    b = encrypt_bytes(data, dek, algo, chunk_size=CS)
    L = get_suite(algo).ct_len(CS)
    spliced = a[:HEADER_LEN] + b[HEADER_LEN : HEADER_LEN + L] + a[HEADER_LEN + L :]
    with pytest.raises(IntegrityError):
        decrypt_bytes(spliced, dek, algo)


@pytest.mark.parametrize("algo", ALGOS)
def test_algorithm_confusion_rejected(algo):
    dek, data, blob = _make(algo)
    for other in ALGOS:
        if other != algo:
            with pytest.raises(IntegrityError):
                decrypt_bytes(blob, dek, other)


def test_garbage_input_rejected():
    dek = new_key()
    for junk in (b"", b"KLNK", os.urandom(500)):
        with pytest.raises(IntegrityError):
            decrypt_bytes(junk, dek)
