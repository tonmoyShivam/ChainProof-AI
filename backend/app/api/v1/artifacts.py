"""Minimal artifact hash/upload endpoints for Milestone 2."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.schemas.artifacts import ErrorResponse, HashResponse, UploadStoreResponse
from app.services.hashing import sha256_hex_of_bytes
from app.services.validation import UploadValidationError, read_and_validate_upload
from app.storage.local import StorageError, store_bytes

router = APIRouter(prefix="/artifacts")


def _error(status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error_code=code, detail=detail).model_dump(),
    )


@router.post(
    "/hash",
    response_model=HashResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
    summary="Compute SHA-256 of an uploaded file (no storage)",
)
async def hash_artifact(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> HashResponse | JSONResponse:
    """Server-side SHA-256 only — never accepts a client-supplied fingerprint."""
    try:
        validated, data = await read_and_validate_upload(file, settings)
    except UploadValidationError as exc:
        status = 413 if exc.code == "FILE_TOO_LARGE" else 400
        return _error(status, exc.code, str(exc))

    digest = sha256_hex_of_bytes(data)
    return HashResponse(
        sha256_hex=digest,
        size_bytes=validated.size_bytes,
        filename=validated.original_filename,
    )


@router.post(
    "/upload",
    response_model=UploadStoreResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}},
    summary="Validate, hash, and store an artifact locally",
)
async def upload_artifact(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> UploadStoreResponse | JSONResponse:
    """Validate type/size, hash server-side, and write under storage/artifacts/."""
    try:
        validated, data = await read_and_validate_upload(file, settings)
        digest = sha256_hex_of_bytes(data)
        stored = store_bytes(
            data,
            extension=validated.extension,
            sha256_hex=digest,
            settings=settings,
        )
    except UploadValidationError as exc:
        status = 413 if exc.code == "FILE_TOO_LARGE" else 400
        return _error(status, exc.code, str(exc))
    except StorageError as exc:
        return _error(500, "STORAGE_ERROR", str(exc))

    return UploadStoreResponse(
        artifact_id=stored.artifact_id,
        sha256_hex=stored.sha256_hex,
        size_bytes=stored.size_bytes,
        original_filename=validated.original_filename,
        stored_relative_path=stored.relative_path,
        content_type=validated.content_type,
    )
