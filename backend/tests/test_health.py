"""Smoke tests for Milestone 1 health endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "VerityAI"


def test_blockchain_health_reports_status() -> None:
    """Must return a structured status; may be unavailable if no local node."""
    response = client.get("/api/v1/health/blockchain")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "unavailable"}
    assert "connected" in payload
    assert "rpc_url" in payload
    assert "detail" in payload
