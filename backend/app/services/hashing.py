"""Chunked SHA-256 hashing for model artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO, Final

DEFAULT_CHUNK_SIZE: Final[int] = 1024 * 1024  # 1 MiB


def sha256_hex_of_stream(
    stream: BinaryIO,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """Compute SHA-256 of a binary stream without loading it entirely into memory."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    digest = hashlib.sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        digest.update(chunk)
    return digest.hexdigest()


def sha256_hex_of_bytes(data: bytes) -> str:
    """Compute SHA-256 of an in-memory byte sequence (tests / small buffers)."""
    return hashlib.sha256(data).hexdigest()


def sha256_hex_of_path(
    path: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> str:
    """Compute SHA-256 of a file on disk using chunked reads."""
    with path.open("rb") as handle:
        return sha256_hex_of_stream(handle, chunk_size=chunk_size)
