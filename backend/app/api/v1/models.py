"""Model registration, history, and verification endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.db import get_session
from app.models.model import Model
from app.models.model_version import ModelVersion
from app.models.user import User
from app.repositories import models as models_repo
from app.repositories import verifications as verifications_repo
from app.schemas.models import (
    ErrorResponse,
    ModelDetailResponse,
    ModelRegistrationResponse,
    ModelVersionResponse,
    VerificationLogResponse,
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


def _version_response(version: ModelVersion) -> ModelVersionResponse:
    return ModelVersionResponse(
        id=version.id,
        on_chain_model_id=version.on_chain_model_id,
        version_number=version.version_number,
        parent_version_id=version.parent_version_id,
        sha256_hash=version.sha256_hash,
        metadata_hash=version.metadata_hash,
        framework=version.framework,
        framework_version=version.framework_version,
        architecture=version.architecture,
        storage_path=version.storage_path,
        storage_type=version.storage_type,
        contract_address=version.contract_address,
        chain_id=version.chain_id,
        transaction_hash=version.transaction_hash,
        block_number=version.block_number,
        registration_status=version.registration_status,
        registered_at=version.registered_at,
    )


def _registration_response(
    family: Model,
    version: ModelVersion,
    *,
    parent_on_chain_id: str | None = None,
) -> ModelRegistrationResponse:
    return ModelRegistrationResponse(
        model_id=version.on_chain_model_id,
        name=family.name,
        description=family.description,
        version_label=str(version.version_number),
        on_chain_version=version.version_number,
        parent_model_id=parent_on_chain_id,
        sha256_hash=version.sha256_hash,
        metadata_hash=version.metadata_hash,
        storage_path=version.storage_path,
        creator_user_id=family.creator_user_id,
        creator_wallet=family.creator_wallet,
        contract_address=version.contract_address,
        chain_id=version.chain_id,
        transaction_hash=version.transaction_hash,
        block_number=version.block_number,
        registration_status="confirmed",
        framework=version.framework,
        framework_version=version.framework_version,
        architecture=version.architecture,
        created_at=version.registered_at,
    )


def _registration_status_code(code: str) -> int:
    if code in {"BLOCKCHAIN_UNAVAILABLE", "BLOCKCHAIN_CONFIG"}:
        return 503
    if code == "TRANSACTION_FAILED":
        return 502
    if code == "UNAUTHORIZED":
        return 403
    if code == "MODEL_NOT_FOUND":
        return 404
    if code == "FILE_TOO_LARGE":
        return 413
    return 400


@router.post(
    "/register",
    response_model=ModelRegistrationResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def register_model(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    version: str = Form("1"),
    framework: str = Form(""),
    framework_version: str = Form(""),
    architecture: str = Form(""),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ModelRegistrationResponse | JSONResponse:
    try:
        result = await register_root_model(
            upload=file,
            name=name,
            description=description,
            version_label=version,
            framework=framework,
            framework_version=framework_version,
            architecture=architecture,
            settings=settings,
            session=session,
            user=user,
        )
    except RegistrationError as exc:
        return _error(_registration_status_code(exc.code), exc.code, str(exc))
    return _registration_response(result.family, result.version)


@router.post(
    "/verify",
    response_model=VerificationResponse,
    responses={400: {"model": ErrorResponse}},
)
async def verify_model(
    model_id: str = Form(...),
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
) -> VerificationResponse | JSONResponse:
    try:
        result = await verify_uploaded_model(
            model_id_hex=model_id,
            upload=file,
            settings=settings,
            session=session,
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


@router.get("", response_model=list[ModelDetailResponse])
async def list_models(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> list[ModelDetailResponse]:
    families = models_repo.list_families(session)
    items: list[ModelDetailResponse] = []
    for family in families:
        versions = sorted(family.versions, key=lambda v: v.version_number)
        latest = versions[-1] if versions else None
        items.append(
            ModelDetailResponse(
                model_id=family.model_id,
                name=family.name,
                description=family.description,
                creator_user_id=family.creator_user_id,
                creator_wallet=family.creator_wallet,
                current_version=family.current_version,
                created_at=family.created_at,
                updated_at=family.updated_at,
                latest_version=_version_response(latest) if latest else None,
            )
        )
    return items


@router.get(
    "/{model_id}",
    response_model=ModelDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_model(
    model_id: str,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> ModelDetailResponse | JSONResponse:
    family = models_repo.resolve_family(session, model_id)
    if family is None:
        return _error(404, "MODEL_NOT_FOUND", "Model not found")
    versions = models_repo.list_versions_for_family(session, family.id)
    latest = versions[-1] if versions else None
    return ModelDetailResponse(
        model_id=family.model_id,
        name=family.name,
        description=family.description,
        creator_user_id=family.creator_user_id,
        creator_wallet=family.creator_wallet,
        current_version=family.current_version,
        created_at=family.created_at,
        updated_at=family.updated_at,
        latest_version=_version_response(latest) if latest else None,
    )


@router.get(
    "/{model_id}/history",
    response_model=list[ModelVersionResponse],
    responses={404: {"model": ErrorResponse}},
)
async def model_history(
    model_id: str,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> list[ModelVersionResponse] | JSONResponse:
    family = models_repo.resolve_family(session, model_id)
    if family is None:
        return _error(404, "MODEL_NOT_FOUND", "Model not found")
    versions = models_repo.list_versions_for_family(session, family.id)
    return [_version_response(v) for v in versions]


@router.get(
    "/{model_id}/verification-history",
    response_model=list[VerificationLogResponse],
    responses={404: {"model": ErrorResponse}},
)
async def verification_history(
    model_id: str,
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> list[VerificationLogResponse] | JSONResponse:
    family = models_repo.resolve_family(session, model_id)
    version = models_repo.get_version_by_on_chain_id(session, model_id)
    if family is None and version is None:
        return _error(404, "MODEL_NOT_FOUND", "Model not found")

    # Collect logs for the family root id and each version on-chain id.
    ids = set()
    if family is not None:
        ids.add(family.model_id)
        for item in models_repo.list_versions_for_family(session, family.id):
            ids.add(item.on_chain_model_id)
    if version is not None:
        ids.add(version.on_chain_model_id)

    logs = []
    for mid in ids:
        logs.extend(verifications_repo.list_for_model_id(session, mid))
    logs.sort(key=lambda log: log.created_at, reverse=True)

    return [
        VerificationLogResponse(
            id=log.id,
            model_version_id=log.model_version_id,
            requested_model_id=log.requested_model_id,
            provided_hash=log.provided_hash,
            expected_hash=log.expected_hash,
            result=log.result,
            error_code=log.error_code,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.post(
    "/{model_id}/versions",
    response_model=ModelRegistrationResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def register_version(
    model_id: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    version: str = Form(""),
    framework: str = Form(""),
    framework_version: str = Form(""),
    architecture: str = Form(""),
    settings: Settings = Depends(get_settings),
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> ModelRegistrationResponse | JSONResponse:
    try:
        result = await register_model_version(
            parent_model_id_hex=model_id,
            upload=file,
            description=description,
            version_label=version,
            framework=framework,
            framework_version=framework_version,
            architecture=architecture,
            settings=settings,
            session=session,
            user=user,
        )
    except RegistrationError as exc:
        return _error(_registration_status_code(exc.code), exc.code, str(exc))

    parent_on_chain = None
    if result.version.parent_version_id:
        parent = session.get(ModelVersion, result.version.parent_version_id)
        if parent is not None:
            parent_on_chain = parent.on_chain_model_id
    return _registration_response(
        result.family,
        result.version,
        parent_on_chain_id=parent_on_chain,
    )
