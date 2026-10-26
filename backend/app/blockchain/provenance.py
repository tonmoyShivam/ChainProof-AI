"""ModelProvenance contract interactions via Web3.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError, TimeExhausted, Web3Exception
from web3.types import TxReceipt

from app.blockchain.client import (
    BlockchainConfigError,
    BlockchainSession,
    BlockchainUnavailableError,
    open_blockchain_session,
    require_contract_address,
)
from app.core.config import Settings

_ABI_PATH = Path(__file__).resolve().parent / "abi" / "ModelProvenance.json"


@dataclass(frozen=True)
class OnChainModel:
    model_id: bytes
    model_hash: bytes
    metadata_hash: bytes
    creator: str
    version: int
    parent_model_id: bytes
    timestamp: int
    exists: bool


@dataclass(frozen=True)
class ConfirmedTransaction:
    transaction_hash: str
    block_number: int
    status: int
    gas_used: int


class ContractTransactionError(RuntimeError):
    """On-chain call reverted or receipt indicated failure."""


def load_contract_abi() -> list[dict[str, Any]]:
    payload = json.loads(_ABI_PATH.read_text(encoding="utf-8"))
    return payload["abi"]


def get_provenance_contract(w3: Web3, settings: Settings) -> Contract:
    address = require_contract_address(settings)
    return w3.eth.contract(address=address, abi=load_contract_abi())


def _send_contract_tx(
    *,
    session: BlockchainSession,
    contract: Contract,
    function_name: str,
    args: tuple[Any, ...],
    timeout: int,
) -> ConfirmedTransaction:
    w3 = session.w3
    account: LocalAccount = session.account
    fn = getattr(contract.functions, function_name)(*args)

    try:
        nonce = w3.eth.get_transaction_count(account.address)
        tx = fn.build_transaction(
            {
                "from": account.address,
                "nonce": nonce,
                "chainId": session.chain_id,
                "gas": 500_000,
            }
        )
        # Let the node suggest fees when available.
        if "gasPrice" not in tx and "maxFeePerGas" not in tx:
            tx["gasPrice"] = w3.eth.gas_price

        signed = account.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = w3.eth.send_raw_transaction(raw)
        receipt: TxReceipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
    except TimeExhausted as exc:
        raise BlockchainUnavailableError("Timed out waiting for transaction receipt") from exc
    except ContractLogicError as exc:
        raise ContractTransactionError(f"Contract reverted: {exc}") from exc
    except (Web3Exception, OSError, TimeoutError, ValueError) as exc:
        raise BlockchainUnavailableError(
            f"Transaction submission failed: {exc.__class__.__name__}: {exc}"
        ) from exc

    status = int(receipt.get("status", 0))
    tx_hex = receipt["transactionHash"].hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex
    if status != 1:
        raise ContractTransactionError(
            f"Transaction failed on-chain (status={status}, tx={tx_hex})"
        )

    return ConfirmedTransaction(
        transaction_hash=tx_hex,
        block_number=int(receipt["blockNumber"]),
        status=status,
        gas_used=int(receipt["gasUsed"]),
    )


def register_model_on_chain(
    *,
    settings: Settings,
    model_id: bytes,
    model_hash: bytes,
    metadata_hash: bytes,
    timeout: int | None = None,
) -> ConfirmedTransaction:
    session = open_blockchain_session(settings)
    contract = get_provenance_contract(session.w3, settings)
    return _send_contract_tx(
        session=session,
        contract=contract,
        function_name="registerModel",
        args=(model_id, model_hash, metadata_hash),
        timeout=timeout or settings.blockchain_tx_timeout_seconds,
    )


def register_version_on_chain(
    *,
    settings: Settings,
    model_id: bytes,
    model_hash: bytes,
    metadata_hash: bytes,
    parent_model_id: bytes,
    version: int,
    timeout: int | None = None,
) -> ConfirmedTransaction:
    session = open_blockchain_session(settings)
    contract = get_provenance_contract(session.w3, settings)
    return _send_contract_tx(
        session=session,
        contract=contract,
        function_name="registerVersion",
        args=(model_id, model_hash, metadata_hash, parent_model_id, version),
        timeout=timeout or settings.blockchain_tx_timeout_seconds,
    )


def get_model_from_chain(*, settings: Settings, model_id: bytes) -> OnChainModel:
    try:
        session = open_blockchain_session(settings)
        contract = get_provenance_contract(session.w3, settings)
        result = contract.functions.getModel(model_id).call()
    except ContractLogicError as exc:
        # ModelNotFound custom error surfaces as ContractLogicError
        raise LookupError("MODEL_NOT_FOUND") from exc
    except BlockchainConfigError:
        raise
    except (Web3Exception, OSError, TimeoutError, ValueError, BlockchainUnavailableError) as exc:
        raise BlockchainUnavailableError(
            f"Failed to read model from chain: {exc.__class__.__name__}"
        ) from exc

    return OnChainModel(
        model_id=bytes(result[0]),
        model_hash=bytes(result[1]),
        metadata_hash=bytes(result[2]),
        creator=result[3],
        version=int(result[4]),
        parent_model_id=bytes(result[5]),
        timestamp=int(result[6]),
        exists=bool(result[7]),
    )


def verify_model_on_chain(
    *,
    settings: Settings,
    model_id: bytes,
    model_hash: bytes,
) -> bool:
    try:
        session = open_blockchain_session(settings)
        contract = get_provenance_contract(session.w3, settings)
        return bool(contract.functions.verifyModel(model_id, model_hash).call())
    except ContractLogicError as exc:
        raise LookupError("MODEL_NOT_FOUND") from exc
    except BlockchainConfigError:
        raise
    except (Web3Exception, OSError, TimeoutError, ValueError, BlockchainUnavailableError) as exc:
        raise BlockchainUnavailableError(
            f"Failed to verify model on chain: {exc.__class__.__name__}"
        ) from exc
