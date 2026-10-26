"""Integrity verification against on-chain fingerprints with DB logging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.blockchain.client import BlockchainConfigError, BlockchainUnavailableError
from app.blockchain.ids import bytes32_to_hex, hex_to_bytes32, sha256_hex_to_bytes32
from app.blockchain.provenance import get_model_from_chain, verify_model_on_chain
from app.core.config import Settings
from app.models.verification_log import VerificationLog
from app.repositories import models as models_repo
from app.repositories import verifications as verifications_repo
from app.services.hashing import sha256_hex_of_bytes
from app.services.validation import UploadValidationError, read_and_validate_upload

VerificationStatus = Literal[
    "VERIFIED",
    "INTEGRITY_MISMATCH",
    "MODEL_NOT_FOUND",
    "VERIFICATION_UNAVAILABLE",
]


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    model_id: str
    expected_hash: str | None
    actual_hash: str | None
    detail: str
    creator_wallet: str | None = None
    on_chain_version: int | None = None


class VerificationError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


async def verify_uploaded_model(
    *,
    model_id_hex: str,
    upload: UploadFile,
    settings: Settings,
    session: Session,
) -> VerificationResult:
    try:
        _validated, data = await read_and_validate_upload(upload, settings)
    except UploadValidationError as exc:
        raise VerificationError(exc.code, str(exc)) from exc

    actual_hash = sha256_hex_of_bytes(data)

    try:
        model_id = hex_to_bytes32(model_id_hex)
        model_hash = sha256_hex_to_bytes32(actual_hash)
    except ValueError as exc:
        raise VerificationError("INVALID_MODEL_ID", str(exc)) from exc

    version_row = models_repo.get_version_by_on_chain_id(session, model_id_hex)
    version_pk = version_row.id if version_row else None

    try:
        on_chain = get_model_from_chain(settings=settings, model_id=model_id)
        matched = verify_model_on_chain(
            settings=settings,
            model_id=model_id,
            model_hash=model_hash,
        )
    except LookupError:
        result = VerificationResult(
            status="MODEL_NOT_FOUND",
            model_id=model_id_hex,
            expected_hash=None,
            actual_hash=actual_hash,
            detail="No registered on-chain record exists for this model id",
        )
        verifications_repo.add_log(
            session,
            VerificationLog(
                model_version_id=version_pk,
                requested_model_id=model_id_hex,
                provided_hash=actual_hash,
                expected_hash=None,
                result=result.status,
                error_code="MODEL_NOT_FOUND",
            ),
        )
        return result
    except (BlockchainUnavailableError, BlockchainConfigError) as exc:
        result = VerificationResult(
            status="VERIFICATION_UNAVAILABLE",
            model_id=model_id_hex,
            expected_hash=None,
            actual_hash=actual_hash,
            detail=str(exc),
        )
        verifications_repo.add_log(
            session,
            VerificationLog(
                model_version_id=version_pk,
                requested_model_id=model_id_hex,
                provided_hash=actual_hash,
                expected_hash=None,
                result=result.status,
                error_code="VERIFICATION_UNAVAILABLE",
            ),
        )
        return result

    expected_hash = bytes32_to_hex(on_chain.model_hash)[2:]
    if matched:
        status: VerificationStatus = "VERIFIED"
        detail = "Uploaded artifact fingerprint matches the on-chain record"
        error_code = None
    else:
        status = "INTEGRITY_MISMATCH"
        detail = "Uploaded artifact fingerprint differs from the on-chain record"
        error_code = "INTEGRITY_MISMATCH"

    verifications_repo.add_log(
        session,
        VerificationLog(
            model_version_id=version_pk,
            requested_model_id=model_id_hex,
            provided_hash=actual_hash,
            expected_hash=expected_hash,
            result=status,
            error_code=error_code,
        ),
    )

    return VerificationResult(
        status=status,
        model_id=model_id_hex,
        expected_hash=expected_hash,
        actual_hash=actual_hash,
        detail=detail,
        creator_wallet=on_chain.creator,
        on_chain_version=on_chain.version,
    )
