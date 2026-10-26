"""Orchestrate upload → hash → on-chain registration → persistence."""

from __future__ import annotations

from dataclasses import dataclass

from eth_account.signers.local import LocalAccount
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.blockchain.client import (
    BlockchainConfigError,
    BlockchainUnavailableError,
    require_contract_address,
    require_signer,
)
from app.blockchain.ids import (
    bytes32_to_hex,
    canonical_metadata_digest,
    hex_to_bytes32,
    new_model_id,
    sha256_hex_to_bytes32,
)
from app.blockchain.provenance import (
    ContractTransactionError,
    get_model_from_chain,
    register_model_on_chain,
    register_version_on_chain,
)
from app.core.config import Settings
from app.models.registration import ModelRegistration
from app.repositories import registrations as reg_repo
from app.services.hashing import sha256_hex_of_bytes
from app.services.validation import UploadValidationError, read_and_validate_upload
from app.storage.local import StorageError, store_bytes


class RegistrationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class RegistrationResult:
    record: ModelRegistration


async def register_root_model(
    *,
    upload: UploadFile,
    name: str,
    description: str,
    version_label: str,
    framework: str,
    framework_version: str,
    settings: Settings,
    session: Session,
) -> RegistrationResult:
    if not name.strip():
        raise RegistrationError("INVALID_METADATA", "Model name is required")

    try:
        signer: LocalAccount = require_signer(settings)
        contract_address = require_contract_address(settings)
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    try:
        validated, data = await read_and_validate_upload(upload, settings)
    except UploadValidationError as exc:
        raise RegistrationError(exc.code, str(exc)) from exc

    model_hash_hex = sha256_hex_of_bytes(data)
    metadata = {
        "name": name.strip(),
        "description": description.strip(),
        "version": version_label.strip() or "1",
        "framework": framework.strip(),
        "framework_version": framework_version.strip(),
        "original_filename": validated.original_filename,
        "size_bytes": validated.size_bytes,
    }
    metadata_hash_hex = canonical_metadata_digest(metadata)

    try:
        stored = store_bytes(
            data,
            extension=validated.extension,
            sha256_hex=model_hash_hex,
            settings=settings,
        )
    except StorageError as exc:
        raise RegistrationError("STORAGE_ERROR", str(exc)) from exc

    model_id = new_model_id()
    model_id_hex = bytes32_to_hex(model_id)

    try:
        confirmed = register_model_on_chain(
            settings=settings,
            model_id=model_id,
            model_hash=sha256_hex_to_bytes32(model_hash_hex),
            metadata_hash=sha256_hex_to_bytes32(metadata_hash_hex),
        )
    except BlockchainUnavailableError as exc:
        raise RegistrationError("BLOCKCHAIN_UNAVAILABLE", str(exc)) from exc
    except ContractTransactionError as exc:
        raise RegistrationError("TRANSACTION_FAILED", str(exc)) from exc
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    # Only persist after on-chain confirmation (status checked inside register_model_on_chain).
    record = ModelRegistration(
        model_id=model_id_hex,
        name=name.strip(),
        description=description.strip(),
        version_label=version_label.strip() or "1",
        on_chain_version=1,
        parent_model_id=None,
        sha256_hash=model_hash_hex,
        metadata_hash=metadata_hash_hex,
        storage_path=stored.relative_path,
        artifact_id=stored.artifact_id,
        creator_wallet=signer.address,
        contract_address=contract_address,
        chain_id=settings.blockchain_chain_id,
        transaction_hash=confirmed.transaction_hash,
        block_number=confirmed.block_number,
        registration_status="confirmed",
        framework=framework.strip(),
        framework_version=framework_version.strip(),
    )
    reg_repo.add_registration(session, record)
    return RegistrationResult(record=record)


async def register_model_version(
    *,
    parent_model_id_hex: str,
    upload: UploadFile,
    name: str,
    description: str,
    version_label: str,
    framework: str,
    framework_version: str,
    settings: Settings,
    session: Session,
) -> RegistrationResult:
    parent = reg_repo.get_by_model_id(session, parent_model_id_hex)
    if parent is None:
        # Fall back to chain lookup so verification-only parents still work.
        try:
            on_chain = get_model_from_chain(
                settings=settings,
                model_id=hex_to_bytes32(parent_model_id_hex),
            )
        except LookupError as exc:
            raise RegistrationError("MODEL_NOT_FOUND", "Parent model not found") from exc
        except BlockchainUnavailableError as exc:
            raise RegistrationError("BLOCKCHAIN_UNAVAILABLE", str(exc)) from exc
        except BlockchainConfigError as exc:
            raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc
        parent_version = on_chain.version
        parent_creator = on_chain.creator
        parent_name = name.strip() or "model"
    else:
        parent_version = parent.on_chain_version
        parent_creator = parent.creator_wallet
        parent_name = name.strip() or parent.name

    try:
        signer = require_signer(settings)
        contract_address = require_contract_address(settings)
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    if signer.address.lower() != parent_creator.lower():
        raise RegistrationError(
            "UNAUTHORIZED",
            "Only the lineage creator wallet may register a new version",
        )

    try:
        validated, data = await read_and_validate_upload(upload, settings)
    except UploadValidationError as exc:
        raise RegistrationError(exc.code, str(exc)) from exc

    model_hash_hex = sha256_hex_of_bytes(data)
    next_version = parent_version + 1
    metadata = {
        "name": parent_name,
        "description": description.strip(),
        "version": version_label.strip() or str(next_version),
        "framework": framework.strip(),
        "framework_version": framework_version.strip(),
        "original_filename": validated.original_filename,
        "size_bytes": validated.size_bytes,
        "parent_model_id": parent_model_id_hex,
    }
    metadata_hash_hex = canonical_metadata_digest(metadata)

    try:
        stored = store_bytes(
            data,
            extension=validated.extension,
            sha256_hex=model_hash_hex,
            settings=settings,
        )
    except StorageError as exc:
        raise RegistrationError("STORAGE_ERROR", str(exc)) from exc

    model_id = new_model_id()
    model_id_hex = bytes32_to_hex(model_id)

    try:
        confirmed = register_version_on_chain(
            settings=settings,
            model_id=model_id,
            model_hash=sha256_hex_to_bytes32(model_hash_hex),
            metadata_hash=sha256_hex_to_bytes32(metadata_hash_hex),
            parent_model_id=hex_to_bytes32(parent_model_id_hex),
            version=next_version,
        )
    except BlockchainUnavailableError as exc:
        raise RegistrationError("BLOCKCHAIN_UNAVAILABLE", str(exc)) from exc
    except ContractTransactionError as exc:
        raise RegistrationError("TRANSACTION_FAILED", str(exc)) from exc
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    record = ModelRegistration(
        model_id=model_id_hex,
        name=parent_name,
        description=description.strip(),
        version_label=version_label.strip() or str(next_version),
        on_chain_version=next_version,
        parent_model_id=parent_model_id_hex,
        sha256_hash=model_hash_hex,
        metadata_hash=metadata_hash_hex,
        storage_path=stored.relative_path,
        artifact_id=stored.artifact_id,
        creator_wallet=signer.address,
        contract_address=contract_address,
        chain_id=settings.blockchain_chain_id,
        transaction_hash=confirmed.transaction_hash,
        block_number=confirmed.block_number,
        registration_status="confirmed",
        framework=framework.strip(),
        framework_version=framework_version.strip(),
    )
    reg_repo.add_registration(session, record)
    return RegistrationResult(record=record)
