"""Security hardening checks (JWT production gate + auth rate limit)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security_hardening import SimpleRateLimitMiddleware, enforce_settings_security


def test_production_rejects_default_jwt() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret="change-me-verityai-dev-secret",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        enforce_settings_security(settings)


def test_development_allows_default_jwt() -> None:
    settings = Settings(app_env="development", jwt_secret="change-me-verityai-dev-secret")
    enforce_settings_security(settings)  # warns only


def test_auth_rate_limit_returns_429() -> None:
    app = FastAPI()

    @app.post("/api/v1/auth/login")
    def login() -> dict:
        return {"ok": True}

    app.add_middleware(SimpleRateLimitMiddleware, limit=3, window=60.0)
    client = TestClient(app)
    for _ in range(3):
        assert client.post("/api/v1/auth/login").status_code == 200
    assert client.post("/api/v1/auth/login").status_code == 429
