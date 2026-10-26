"""Helpers for bytes32 identifiers and digests used on-chain."""

from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

from web3 import Web3

from app.services.hashing import sha256_hex_of_bytes


def new_model_id() -> bytes:
    """Generate a unique bytes32 model id (keccak of a UUID4 string)."""
    return Web3.keccak(text=str(uuid.uuid4()))


def bytes32_to_hex(value: bytes | bytearray) -> str:
    return "0x" + bytes(value).hex()


def hex_to_bytes32(value: str) -> bytes:
    raw = value[2:] if value.startswith("0x") else value
    data = bytes.fromhex(raw)
    if len(data) != 32:
        raise ValueError("Expected 32-byte hex value")
    return data


def sha256_hex_to_bytes32(sha256_hex: str) -> bytes:
    """Convert a 64-char SHA-256 hex digest into bytes32."""
    raw = sha256_hex[2:] if sha256_hex.startswith("0x") else sha256_hex
    if len(raw) != 64:
        raise ValueError("SHA-256 hex digest must be 64 characters")
    return bytes.fromhex(raw)


def canonical_metadata_digest(metadata: Mapping[str, Any]) -> str:
    """
    SHA-256 hex of canonical JSON metadata (sorted keys, compact separators).

    Used as the on-chain metadataHash (as bytes32).
    """
    payload = json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_hex_of_bytes(payload.encode("utf-8"))
