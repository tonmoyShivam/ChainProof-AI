"""Shared pytest fixtures for Milestone 5+."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db import reset_db_state
from app.main import app


@pytest.fixture()
def tmp_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "test.db"
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "5")
    monkeypatch.setenv("ALLOWED_UPLOAD_EXTENSIONS", ".pt,.txt,.onnx,.json")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv(
        "BLOCKCHAIN_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )
    get_settings.cache_clear()
    reset_db_state()
    return tmp_path


@pytest.fixture()
def client(tmp_env: Path) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()
    reset_db_state()


def register_and_login(
    client: TestClient,
    *,
    email: str = "dev@example.com",
    password: str = "password123",
    display_name: str = "Dev",
) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert response.status_code == 201, response.text
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]
