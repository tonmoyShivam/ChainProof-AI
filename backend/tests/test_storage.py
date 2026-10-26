"""Tests for safe local artifact storage."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.storage.local import (
    StorageError,
    assert_within_storage,
    build_safe_filename,
    resolve_storage_root,
    store_bytes,
)


def test_store_bytes_uses_uuid_filename(tmp_path: Path) -> None:
    settings = Settings(storage_path=str(tmp_path / "storage"))
    digest = "a" * 64
    stored = store_bytes(
        b"model-bytes",
        extension=".pt",
        sha256_hex=digest,
        settings=settings,
        base=tmp_path,
    )

    assert stored.sha256_hex == digest
    assert stored.relative_path.startswith("artifacts/")
    assert stored.absolute_path.exists()
    assert stored.absolute_path.name == f"{stored.artifact_id}.pt"
    assert ".." not in stored.relative_path
    assert stored.absolute_path.read_bytes() == b"model-bytes"


def test_build_safe_filename_rejects_pathful_extension() -> None:
    with pytest.raises(StorageError):
        build_safe_filename("../pt")


def test_assert_within_storage_blocks_traversal(tmp_path: Path) -> None:
    root = resolve_storage_root(
        Settings(storage_path=str(tmp_path / "storage")),
        base=tmp_path,
    )
    with pytest.raises(StorageError):
        assert_within_storage(root, root / ".." / "outside.bin")
