"""Model registration and verification endpoints (Milestone 4)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.blockchain.client import BlockchainConfigError, BlockchainUnavailableError
from app.blockchain.ids import bytes32_to_hex, hex_to_bytes32
from app.blockchain.provenance import get_model_from_chain
from app.core.config import Settings, get_settings
from app.db import get_session
from app.repositories import registrations as reg_repo
from app.schemas.models import (
    ErrorResponse,
    ModelRegistrationResponse,
    VerificationResponse,
)
from app.services.registration import RegistrationError, register_model_version, register_root_model
from app.services.verification import VerificationError, verify_uploaded_model

router = APIRouter(prefix="/models")


def _error(status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error_code=code, detail=detail).model_dump(),
    )


def _registration_response(record) -> ModelRegistrationResponse:
    return ModelRegistrationResponse(
        model_id=record.model_id,
        name=record.name,
        description=record.description,
        version_label=record.version_label,
        on_chain_version=record.on_chain_version,
        parent_model_id=record.parent_model_id,
        sha256_hash=record.sha256_hash,
        metadata_hash=record.metadata_hash,
        storage_path=record.storage_path,
        creator_wallet=record.creator_wallet,
        contract_address=record.contract_address,
        chain_id=record.chain_id,
        transaction_hash=record.transaction_hash,
        block_number=record.block_number,
        registration_status="confirmed",
        framework=record.framework,
        framework_version=record.framework_version,
        created_at=record.created_at,
    )


@router.post(
    "/register",
    response_model=ModelRegistrationResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def register_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    version: str = Form("1"),
    framework: str = Form(""),
    framework_version: str = Form(""),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> ModelRegistrationResponse | JSONResponse:
    """
    Validate + hash + store the artifact, submit `registerModel`, wait for
    confirmation, then persist. Never returns success before confirmation.
    """
    try:
        result = await register_root_model(
            upload=file,
            name=name,
            description=description,
            version_label=version,
            framework=framework,
            framework_version=framework_version,
            settings=settings,
            session=session,
        )
    except RegistrationError as exc:
        status = 503 if exc.code in {"BLOCKCHAIN_UNAVAILABLE", "BLOCKCHAIN_CONFIG"} else 400
        if exc.code == "TRANSACTION_FAILED":
            status = 502
        if exc.code == "FILE_TOO_LARGE":
            status = 413
        return _error(status, exc.code, str(exc))

    return _registration_response(result.record)


@router.post(
    "/verify",
    response_model=VerificationResponse,
    responses={400: {"model": ErrorResponse}},
)
async def verify_model(
    model_id: str = Form(...),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> VerificationResponse | JSONResponse:
    """Compare an uploaded artifact against the authoritative on-chain fingerprint."""
    try:
        result = await verify_uploaded_model(
            model_id_hex=model_id,
            upload=file,
            settings=settings,
        )
    except VerificationError as exc:
        status = 413 if exc.code == "FILE_TOO_LARGE" else 400
        return _error(status, exc.code, str(exc))

    http_status = 503 if result.status == "VERIFICATION_UNAVAILABLE" else 200
    return JSONResponse(
        status_code=http_status,
        content=VerificationResponse(
            status=result.status,
            model_id=result.model_id,
            expected_hash=result.expected_hash,
            actual_hash=result.actual_hash,
            detail=result.detail,
            creator_wallet=result.creator_wallet,
            on_chain_version=result.on_chain_version,
        ).model_dump(),
    )


@router.get("", response_model=list[ModelRegistrationResponse])
async def list_models(
    session: Session = Depends(get_session),
) -> list[ModelRegistrationResponse]:
    records = reg_repo.list_registrations(session)
    return [_registration_response(record) for record in records]


@router.get(
    "/{model_id}",
    response_model=ModelRegistrationResponse,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def get_model(
    model_id: str,
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> ModelRegistrationResponse | JSONResponse:
    """Return persisted registration metadata, with chain fallback when needed."""
    record = reg_repo.get_by_model_id(session, model_id)
    if record is not None:
        return _registration_response(record)

    try:
        on_chain = get_model_from_chain(
            settings=settings,
            model_id=hex_to_bytes32(model_id),
        )
    except LookupError:
        return _error(404, "MODEL_NOT_FOUND", "Model not found")
    except ValueError as exc:
        return _error(400, "INVALID_MODEL_ID", str(exc))
    except (BlockchainUnavailableError, BlockchainConfigError) as exc:
        return _error(503, "BLOCKCHAIN_UNAVAILABLE", str(exc))

    zero = b"\x00" * 32
    return ModelRegistrationResponse(
        model_id=bytes32_to_hex(on_chain.model_id),
        name="(on-chain only)",
        description="",
        version_label=str(on_chain.version),
        on_chain_version=on_chain.version,
        parent_model_id=(
            bytes32_to_hex(on_chain.parent_model_id)
            if on_chain.parent_model_id != zero
            else None
        ),
        sha256_hash=bytes32_to_hex(on_chain.model_hash)[2:],
        metadata_hash=bytes32_to_hex(on_chain.metadata_hash)[2:],
        storage_path="",
        creator_wallet=on_chain.creator,
        contract_address=settings.blockchain_contract_address,
        chain_id=settings.blockchain_chain_id,
        transaction_hash="",
        block_number=0,
        registration_status="confirmed",
        created_at=datetime.fromtimestamp(on_chain.timestamp, tz=timezone.utc),
    )


@router.post(
    "/{model_id}/versions",
    response_model=ModelRegistrationResponse,
    responses={400: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def register_version(
    model_id: str,
    file: UploadFile = File(...),
    name: str = Form(""),
    description: str = Form(""),
    version: str = Form(""),
    framework: str = Form(""),
    framework_version: str = Form(""),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> ModelRegistrationResponse | JSONResponse:
    try:
        result = await register_model_version(
            parent_model_id_hex=model_id,
            upload=file,
            name=name,
            description=description,
            version_label=version,
            framework=framework,
            framework_version=framework_version,
            settings=settings,
            session=session,
        )
    except RegistrationError as exc:
        status = 503 if exc.code in {"BLOCKCHAIN_UNAVAILABLE", "BLOCKCHAIN_CONFIG"} else 400
        if exc.code == "TRANSACTION_FAILED":
            status = 502
        if exc.code == "UNAUTHORIZED":
            status = 403
        if exc.code == "MODEL_NOT_FOUND":
            status = 404
        return _error(status, exc.code, str(exc))

    return _registration_response(result.record)
