"""Orchestrate upload → hash → on-chain registration → DB persistence."""

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
from app.models.model import Model
from app.models.model_version import ModelVersion
from app.models.user import User
from app.repositories import models as models_repo
from app.services.hashing import sha256_hex_of_bytes
from app.services.validation import UploadValidationError, read_and_validate_upload
from app.storage.local import StorageError, store_bytes


class RegistrationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class RegistrationResult:
    family: Model
    version: ModelVersion


async def register_root_model(
    *,
    upload: UploadFile,
    name: str,
    description: str,
    version_label: str,
    framework: str,
    framework_version: str,
    architecture: str,
    settings: Settings,
    session: Session,
    user: User,
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
        "architecture": architecture.strip(),
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

    on_chain_id = new_model_id()
    on_chain_id_hex = bytes32_to_hex(on_chain_id)

    try:
        confirmed = register_model_on_chain(
            settings=settings,
            model_id=on_chain_id,
            model_hash=sha256_hex_to_bytes32(model_hash_hex),
            metadata_hash=sha256_hex_to_bytes32(metadata_hash_hex),
        )
    except BlockchainUnavailableError as exc:
        raise RegistrationError("BLOCKCHAIN_UNAVAILABLE", str(exc)) from exc
    except ContractTransactionError as exc:
        raise RegistrationError("TRANSACTION_FAILED", str(exc)) from exc
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    family = Model(
        model_id=on_chain_id_hex,
        name=name.strip(),
        description=description.strip(),
        creator_user_id=user.id,
        creator_wallet=signer.address,
        current_version=1,
    )
    models_repo.add_family(session, family)

    version = ModelVersion(
        model_family_id=family.id,
        on_chain_model_id=on_chain_id_hex,
        version_number=1,
        parent_version_id=None,
        sha256_hash=model_hash_hex,
        metadata_hash=metadata_hash_hex,
        framework=framework.strip(),
        framework_version=framework_version.strip(),
        architecture=architecture.strip(),
        storage_path=stored.relative_path,
        storage_type="local",
        contract_address=contract_address,
        chain_id=settings.blockchain_chain_id,
        transaction_hash=confirmed.transaction_hash,
        block_number=confirmed.block_number,
        registration_status="confirmed",
    )
    models_repo.add_version(session, version)
    return RegistrationResult(family=family, version=version)


async def register_model_version(
    *,
    parent_model_id_hex: str,
    upload: UploadFile,
    description: str,
    version_label: str,
    framework: str,
    framework_version: str,
    architecture: str,
    settings: Settings,
    session: Session,
    user: User,
) -> RegistrationResult:
    family = models_repo.resolve_family(session, parent_model_id_hex)
    if family is None:
        try:
            get_model_from_chain(
                settings=settings,
                model_id=hex_to_bytes32(parent_model_id_hex),
            )
        except LookupError as exc:
            raise RegistrationError("MODEL_NOT_FOUND", "Parent model not found") from exc
        except BlockchainUnavailableError as exc:
            raise RegistrationError("BLOCKCHAIN_UNAVAILABLE", str(exc)) from exc
        except BlockchainConfigError as exc:
            raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc
        except ValueError as exc:
            raise RegistrationError("INVALID_MODEL_ID", str(exc)) from exc
        raise RegistrationError(
            "MODEL_NOT_FOUND",
            "Parent exists on-chain but is not in the local database; register the root first",
        )

    if family.creator_user_id != user.id and user.role != "admin":
        raise RegistrationError("UNAUTHORIZED", "Only the model creator may register a new version")

    try:
        signer = require_signer(settings)
        contract_address = require_contract_address(settings)
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    if signer.address.lower() != family.creator_wallet.lower():
        raise RegistrationError(
            "UNAUTHORIZED",
            "Configured signer wallet must match the lineage creator wallet",
        )

    parent_version = None
    for item in models_repo.list_versions_for_family(session, family.id):
        if item.on_chain_model_id == parent_model_id_hex or item.version_number == family.current_version:
            parent_version = item
    if parent_version is None:
        versions = models_repo.list_versions_for_family(session, family.id)
        parent_version = versions[-1] if versions else None
    if parent_version is None:
        raise RegistrationError("MODEL_NOT_FOUND", "Parent version not found in database")

    # Prefer explicit parent when the path param is a version on-chain id.
    explicit = models_repo.get_version_by_on_chain_id(session, parent_model_id_hex)
    if explicit is not None:
        parent_version = explicit

    try:
        validated, data = await read_and_validate_upload(upload, settings)
    except UploadValidationError as exc:
        raise RegistrationError(exc.code, str(exc)) from exc

    model_hash_hex = sha256_hex_of_bytes(data)
    next_version = parent_version.version_number + 1
    metadata = {
        "name": family.name,
        "description": description.strip(),
        "version": version_label.strip() or str(next_version),
        "framework": framework.strip() or parent_version.framework,
        "framework_version": framework_version.strip() or parent_version.framework_version,
        "architecture": architecture.strip() or parent_version.architecture,
        "original_filename": validated.original_filename,
        "size_bytes": validated.size_bytes,
        "parent_model_id": parent_version.on_chain_model_id,
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

    on_chain_id = new_model_id()
    on_chain_id_hex = bytes32_to_hex(on_chain_id)

    try:
        confirmed = register_version_on_chain(
            settings=settings,
            model_id=on_chain_id,
            model_hash=sha256_hex_to_bytes32(model_hash_hex),
            metadata_hash=sha256_hex_to_bytes32(metadata_hash_hex),
            parent_model_id=hex_to_bytes32(parent_version.on_chain_model_id),
            version=next_version,
        )
    except BlockchainUnavailableError as exc:
        raise RegistrationError("BLOCKCHAIN_UNAVAILABLE", str(exc)) from exc
    except ContractTransactionError as exc:
        raise RegistrationError("TRANSACTION_FAILED", str(exc)) from exc
    except BlockchainConfigError as exc:
        raise RegistrationError("BLOCKCHAIN_CONFIG", str(exc)) from exc

    version = ModelVersion(
        model_family_id=family.id,
        on_chain_model_id=on_chain_id_hex,
        version_number=next_version,
        parent_version_id=parent_version.id,
        sha256_hash=model_hash_hex,
        metadata_hash=metadata_hash_hex,
        framework=framework.strip() or parent_version.framework,
        framework_version=framework_version.strip() or parent_version.framework_version,
        architecture=architecture.strip() or parent_version.architecture,
        storage_path=stored.relative_path,
        storage_type="local",
        contract_address=contract_address,
        chain_id=settings.blockchain_chain_id,
        transaction_hash=confirmed.transaction_hash,
        block_number=confirmed.block_number,
        registration_status="confirmed",
    )
    models_repo.add_version(session, version)
    family.current_version = next_version
    return RegistrationResult(family=family, version=version)
