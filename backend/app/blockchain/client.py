"""Web3 connection helpers for the local Hardhat EVM."""

from __future__ import annotations

from dataclasses import dataclass

from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.exceptions import Web3Exception
from web3.providers.rpc import HTTPProvider

from app.core.config import Settings


class BlockchainUnavailableError(RuntimeError):
    """RPC / chain is unreachable or misconfigured."""


class BlockchainConfigError(RuntimeError):
    """Missing or invalid blockchain configuration."""


@dataclass(frozen=True)
class BlockchainSession:
    w3: Web3
    account: LocalAccount
    chain_id: int


def connect_web3(settings: Settings, *, timeout: float = 5.0) -> Web3:
    provider = HTTPProvider(settings.blockchain_rpc_url, request_kwargs={"timeout": timeout})
    return Web3(provider)


def require_connected_web3(settings: Settings, *, timeout: float = 5.0) -> Web3:
    try:
        w3 = connect_web3(settings, timeout=timeout)
        if not w3.is_connected():
            raise BlockchainUnavailableError("Blockchain RPC is not connected")
        return w3
    except (Web3Exception, OSError, TimeoutError, ValueError) as exc:
        raise BlockchainUnavailableError(
            f"Blockchain RPC unreachable: {exc.__class__.__name__}"
        ) from exc


def require_signer(settings: Settings) -> LocalAccount:
    key = (settings.blockchain_private_key or "").strip()
    if not key:
        raise BlockchainConfigError(
            "BLOCKCHAIN_PRIVATE_KEY is not configured (use a Hardhat test key locally)"
        )
    if not key.startswith("0x"):
        key = "0x" + key
    try:
        return Account.from_key(key)
    except ValueError as exc:
        raise BlockchainConfigError("BLOCKCHAIN_PRIVATE_KEY is invalid") from exc


def require_contract_address(settings: Settings) -> str:
    address = (settings.blockchain_contract_address or "").strip()
    if not address:
        raise BlockchainConfigError(
            "BLOCKCHAIN_CONTRACT_ADDRESS is not set — deploy ModelProvenance first"
        )
    try:
        return Web3.to_checksum_address(address)
    except ValueError as exc:
        raise BlockchainConfigError("BLOCKCHAIN_CONTRACT_ADDRESS is invalid") from exc


def open_blockchain_session(settings: Settings) -> BlockchainSession:
    w3 = require_connected_web3(settings)
    account = require_signer(settings)
    try:
        chain_id = int(w3.eth.chain_id)
    except (Web3Exception, OSError, TimeoutError, ValueError) as exc:
        raise BlockchainUnavailableError(
            f"Failed to read chain id: {exc.__class__.__name__}"
        ) from exc

    if settings.blockchain_chain_id and chain_id != settings.blockchain_chain_id:
        raise BlockchainUnavailableError(
            f"Unexpected chain id {chain_id}; expected {settings.blockchain_chain_id}"
        )
    return BlockchainSession(w3=w3, account=account, chain_id=chain_id)
