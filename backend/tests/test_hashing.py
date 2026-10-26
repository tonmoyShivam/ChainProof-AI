"""Unit tests for chunked SHA-256 hashing and integrity detection."""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

from app.services.hashing import (
    sha256_hex_of_bytes,
    sha256_hex_of_path,
    sha256_hex_of_stream,
)


def test_hash_empty_file() -> None:
    expected = hashlib.sha256(b"").hexdigest()
    assert sha256_hex_of_bytes(b"") == expected
    assert sha256_hex_of_stream(io.BytesIO(b"")) == expected


def test_hash_non_empty_file() -> None:
    payload = b"verityai-model-bytes-v1"
    expected = hashlib.sha256(payload).hexdigest()
    assert sha256_hex_of_bytes(payload) == expected
    assert sha256_hex_of_stream(io.BytesIO(payload), chunk_size=4) == expected


def test_hash_consistency_identical_files(tmp_path: Path) -> None:
    payload = b"identical-artifact" * 1000
    path_a = tmp_path / "a.bin"
    path_b = tmp_path / "b.bin"
    path_a.write_bytes(payload)
    path_b.write_bytes(payload)

    hash_a = sha256_hex_of_path(path_a, chunk_size=64)
    hash_b = sha256_hex_of_path(path_b, chunk_size=1024)
    assert hash_a == hash_b
    assert hash_a == hashlib.sha256(payload).hexdigest()


def test_integrity_detection_after_modification(tmp_path: Path) -> None:
    original = b"ABCDEFGH"
    path = tmp_path / "model.pt"
    path.write_bytes(original)
    original_hash = sha256_hex_of_path(path)

    modified = bytearray(original)
    modified[3] ^= 0x01
    path.write_bytes(bytes(modified))
    modified_hash = sha256_hex_of_path(path)

    assert original_hash != modified_hash
    assert modified_hash == hashlib.sha256(bytes(modified)).hexdigest()
