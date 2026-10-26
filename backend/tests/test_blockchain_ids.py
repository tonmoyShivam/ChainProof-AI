"""Unit tests for on-chain id / metadata digest helpers."""

from app.blockchain.ids import (
    bytes32_to_hex,
    canonical_metadata_digest,
    hex_to_bytes32,
    new_model_id,
    sha256_hex_to_bytes32,
)
from app.services.hashing import sha256_hex_of_bytes


def test_new_model_id_is_32_bytes() -> None:
    value = new_model_id()
    assert len(value) == 32
    assert bytes32_to_hex(value).startswith("0x")


def test_sha256_hex_round_trip() -> None:
    digest = sha256_hex_of_bytes(b"abc")
    raw = sha256_hex_to_bytes32(digest)
    assert len(raw) == 32
    assert raw.hex() == digest


def test_hex_to_bytes32_requires_32_bytes() -> None:
    try:
        hex_to_bytes32("0xabcd")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_canonical_metadata_digest_is_stable() -> None:
    meta_a = {"name": "m", "version": "1", "framework": "torch"}
    meta_b = {"framework": "torch", "version": "1", "name": "m"}
    assert canonical_metadata_digest(meta_a) == canonical_metadata_digest(meta_b)
    assert len(canonical_metadata_digest(meta_a)) == 64
