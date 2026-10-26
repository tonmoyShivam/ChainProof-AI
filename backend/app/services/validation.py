"""Upload validation for model artifacts."""

from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import UploadFile

from app.core.config import Settings


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ValidatedUpload:
    original_filename: str
    extension: str
    size_bytes: int
    content_type: str | None


def _normalize_extension(filename: str) -> str:
    """Return a lowercase extension including the leading dot, or empty string."""
    # Use only the final path segment so directory components cannot influence type checks.
    basename = os.path.basename(filename.replace("\\", "/"))
    if not basename or basename in {".", ".."}:
        raise UploadValidationError(
            "INVALID_FILENAME",
            "Filename is missing or invalid",
        )
    _, ext = os.path.splitext(basename)
    return ext.lower()


def validate_upload_metadata(
    *,
    filename: str | None,
    size_bytes: int,
    content_type: str | None,
    settings: Settings,
) -> ValidatedUpload:
    """Validate filename, size, and declared content type before/after reading body."""
    if not filename or not filename.strip():
        raise UploadValidationError("INVALID_FILENAME", "Filename is required")

    if size_bytes < 0:
        raise UploadValidationError("INVALID_SIZE", "File size cannot be negative")

    max_bytes = settings.max_upload_size_bytes
    if size_bytes > max_bytes:
        raise UploadValidationError(
            "FILE_TOO_LARGE",
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    extension = _normalize_extension(filename)
    allowed = settings.allowed_extension_set
    if extension not in allowed:
        raise UploadValidationError(
            "UNSUPPORTED_FILE_TYPE",
            f"Unsupported file type '{extension or '(none)'}'. "
            f"Allowed: {', '.join(sorted(allowed))}",
        )

    return ValidatedUpload(
        original_filename=os.path.basename(filename.replace("\\", "/")),
        extension=extension,
        size_bytes=size_bytes,
        content_type=content_type,
    )


async def read_and_validate_upload(
    upload: UploadFile,
    settings: Settings,
) -> tuple[ValidatedUpload, bytes]:
    """
    Read the upload into memory up to the configured limit and validate metadata.

    Milestone 2 keeps a bounded in-memory buffer for the HTTP path while hashing
    services remain chunked for on-disk / stream use. Size is enforced before
    accepting the full payload for storage.
    """
    max_bytes = settings.max_upload_size_bytes
    # Read one extra byte to detect oversize without trusting Content-Length alone.
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise UploadValidationError(
            "FILE_TOO_LARGE",
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    validated = validate_upload_metadata(
        filename=upload.filename,
        size_bytes=len(data),
        content_type=upload.content_type,
        settings=settings,
    )
    return validated, data
