"""Integration tests against a live Hardhat node + ModelProvenance deploy."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from eth_account import Account
from fastapi.testclient import TestClient
from web3 import Web3

from app.core.config import get_settings
from app.db import reset_db_state
from app.main import app
from tests.conftest import register_and_login

HARDHAT_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
RPC_URL = "http://127.0.0.1:8545"
ARTIFACT = (
    Path(__file__).resolve().parents[2]
    / "blockchain"
    / "artifacts"
    / "contracts"
    / "ModelProvenance.sol"
    / "ModelProvenance.json"
)


def _hardhat_available() -> bool:
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 2}))
        return bool(w3.is_connected())
    except Exception:
        return False


def _deploy_provenance(w3: Web3) -> str:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    account = Account.from_key(HARDHAT_KEY)
    contract = w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
    tx = contract.constructor(account.address).build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": w3.eth.chain_id,
            "gas": 3_000_000,
            "gasPrice": w3.eth.gas_price,
        }
    )
    signed = account.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    tx_hash = w3.eth.send_raw_transaction(raw)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
    assert receipt["status"] == 1
    return receipt["contractAddress"]


pytestmark = pytest.mark.skipif(
    not _hardhat_available() or not ARTIFACT.exists(),
    reason="Hardhat node or compiled artifact unavailable",
)


@pytest.fixture()
def live_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 5}))
    address = _deploy_provenance(w3)

    db_path = tmp_path / "live.db"
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "5")
    monkeypatch.setenv("ALLOWED_UPLOAD_EXTENSIONS", ".pt,.txt,.onnx")
    monkeypatch.setenv("BLOCKCHAIN_RPC_URL", RPC_URL)
    monkeypatch.setenv("BLOCKCHAIN_CHAIN_ID", str(w3.eth.chain_id))
    monkeypatch.setenv("BLOCKCHAIN_CONTRACT_ADDRESS", address)
    monkeypatch.setenv("BLOCKCHAIN_PRIVATE_KEY", HARDHAT_KEY)
    monkeypatch.setenv("JWT_SECRET", "live-test-secret")
    get_settings.cache_clear()
    reset_db_state()

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    reset_db_state()


def test_register_confirm_and_verify_match(live_client: TestClient) -> None:
    token = register_and_login(live_client, email="chain@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = b"verityai-integration-model-v1"
    register = live_client.post(
        "/api/v1/models/register",
        headers=headers,
        data={
            "name": "Demo Model",
            "description": "integration",
            "version": "1.0.0",
            "framework": "pytorch",
            "framework_version": "2.0",
        },
        files={"file": ("model.pt", payload, "application/octet-stream")},
    )
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["registration_status"] == "confirmed"
    assert body["transaction_hash"].startswith("0x")
    assert body["creator_user_id"]
    model_id = body["model_id"]

    verify = live_client.post(
        "/api/v1/models/verify",
        data={"model_id": model_id},
        files={"file": ("model.pt", payload, "application/octet-stream")},
    )
    assert verify.status_code == 200, verify.text
    result = verify.json()
    assert result["status"] == "VERIFIED"

    history = live_client.get(
        f"/api/v1/models/{model_id}/history",
        headers=headers,
    )
    assert history.status_code == 200
    assert len(history.json()) == 1

    stats = live_client.get("/api/v1/dashboard/stats", headers=headers)
    assert stats.status_code == 200
    assert stats.json()["total_registered_models"] == 1
    assert stats.json()["successful_verifications"] == 1


def test_verify_detects_integrity_mismatch(live_client: TestClient) -> None:
    token = register_and_login(live_client, email="mismatch@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    original = b"ABCDEFGH"
    register = live_client.post(
        "/api/v1/models/register",
        headers=headers,
        data={"name": "Mismatch Demo", "version": "1"},
        files={"file": ("model.pt", original, "application/octet-stream")},
    )
    assert register.status_code == 200, register.text
    model_id = register.json()["model_id"]

    tampered = bytearray(original)
    tampered[0] ^= 0xFF
    verify = live_client.post(
        "/api/v1/models/verify",
        data={"model_id": model_id},
        files={"file": ("model.pt", bytes(tampered), "application/octet-stream")},
    )
    assert verify.status_code == 200, verify.text
    result = verify.json()
    assert result["status"] == "INTEGRITY_MISMATCH"

    vhist = live_client.get(
        f"/api/v1/models/{model_id}/verification-history",
        headers=headers,
    )
    assert vhist.status_code == 200
    assert any(item["result"] == "INTEGRITY_MISMATCH" for item in vhist.json())


def test_register_requires_auth_and_fails_when_rpc_unreachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "fail.db"
    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.setenv("ALLOWED_UPLOAD_EXTENSIONS", ".pt")
    monkeypatch.setenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("BLOCKCHAIN_CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
    monkeypatch.setenv("BLOCKCHAIN_PRIVATE_KEY", HARDHAT_KEY)
    monkeypatch.setenv("JWT_SECRET", "fail-secret")
    get_settings.cache_clear()
    reset_db_state()

    with TestClient(app) as client:
        unauth = client.post(
            "/api/v1/models/register",
            data={"name": "Nope"},
            files={"file": ("model.pt", b"x", "application/octet-stream")},
        )
        assert unauth.status_code == 401

        token = register_and_login(client, email="rpcfail@example.com")
        response = client.post(
            "/api/v1/models/register",
            headers={"Authorization": f"Bearer {token}"},
            data={"name": "Nope"},
            files={"file": ("model.pt", b"x", "application/octet-stream")},
        )
    assert response.status_code == 503
    assert response.json()["error_code"] == "BLOCKCHAIN_UNAVAILABLE"

    get_settings.cache_clear()
    reset_db_state()
