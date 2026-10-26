"""Verification must not report VERIFIED when the blockchain is unreachable."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.blockchain.client import BlockchainUnavailableError
from app.core.config import get_settings
from app.db import reset_db_state
from app.main import app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "1")
    monkeypatch.setenv("ALLOWED_UPLOAD_EXTENSIONS", ".pt,.txt")
    monkeypatch.setenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("BLOCKCHAIN_CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
    monkeypatch.setenv(
        "BLOCKCHAIN_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    get_settings.cache_clear()
    reset_db_state()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    reset_db_state()


def test_verify_returns_unavailable_when_rpc_down(client: TestClient) -> None:
    model_id = "0x" + ("11" * 32)
    with patch(
        "app.services.verification.get_model_from_chain",
        side_effect=BlockchainUnavailableError("RPC down"),
    ):
        response = client.post(
            "/api/v1/models/verify",
            data={"model_id": model_id},
            files={"file": ("weights.pt", b"payload", "application/octet-stream")},
        )
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "VERIFICATION_UNAVAILABLE"
    assert body["status"] != "VERIFIED"
    assert body["actual_hash"] is not None
