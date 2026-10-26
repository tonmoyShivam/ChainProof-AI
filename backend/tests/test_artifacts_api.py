"""API tests for Milestone 2 hash and upload endpoints."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "1")
    monkeypatch.setenv("ALLOWED_UPLOAD_EXTENSIONS", ".pt,.onnx,.json,.txt")
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_hash_endpoint_returns_sha256(client: TestClient) -> None:
    payload = b"hello-verityai"
    response = client.post(
        "/api/v1/artifacts/hash",
        files={"file": ("demo.pt", payload, "application/octet-stream")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["algorithm"] == "sha256"
    assert body["sha256_hex"] == hashlib.sha256(payload).hexdigest()
    assert body["size_bytes"] == len(payload)
    assert body["filename"] == "demo.pt"


def test_hash_endpoint_rejects_bad_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/artifacts/hash",
        files={"file": ("malware.exe", b"x", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_stores_and_hashes(client: TestClient, tmp_path: Path) -> None:
    payload = b"stored-model"
    response = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("weights.onnx", payload, "application/octet-stream")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sha256_hex"] == hashlib.sha256(payload).hexdigest()
    assert body["original_filename"] == "weights.onnx"
    stored = Path(tmp_path / "storage" / body["stored_relative_path"])
    assert stored.exists()
    assert stored.read_bytes() == payload


def test_upload_integrity_mismatch_detected_after_edit(
    client: TestClient,
    tmp_path: Path,
) -> None:
    payload = b"ABCDEFGH"
    response = client.post(
        "/api/v1/artifacts/upload",
        files={"file": ("model.pt", payload, "application/octet-stream")},
    )
    assert response.status_code == 200
    original_hash = response.json()["sha256_hex"]
    stored = Path(tmp_path / "storage" / response.json()["stored_relative_path"])

    altered = bytearray(stored.read_bytes())
    altered[0] ^= 0xFF
    stored.write_bytes(bytes(altered))

    rehash = client.post(
        "/api/v1/artifacts/hash",
        files={"file": ("model.pt", bytes(altered), "application/octet-stream")},
    )
    assert rehash.status_code == 200
    assert rehash.json()["sha256_hex"] != original_hash


def test_upload_rejects_path_traversal_filename(client: TestClient) -> None:
    response = client.post(
        "/api/v1/artifacts/upload",
        files={
            "file": (
                "../../etc/passwd.txt",
                b"not-a-secret",
                "text/plain",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["original_filename"] == "passwd.txt"
    assert ".." not in body["stored_relative_path"]
    assert body["stored_relative_path"].startswith("artifacts/")
