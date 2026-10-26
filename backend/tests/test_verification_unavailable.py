"""Verification must not report VERIFIED when the blockchain is unreachable."""

from __future__ import annotations

from unittest.mock import patch

from app.blockchain.client import BlockchainUnavailableError


def test_verify_returns_unavailable_when_rpc_down(client) -> None:
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
