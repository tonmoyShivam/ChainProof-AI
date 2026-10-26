"""Tests for upload validation rules."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.services.validation import UploadValidationError, validate_upload_metadata


def _settings(**overrides: object) -> Settings:
    base = {
        "max_upload_size_mb": 1,
        "allowed_upload_extensions": ".pt,.onnx,.json,.txt",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


def test_accepts_allowed_extension() -> None:
    result = validate_upload_metadata(
        filename="model.pt",
        size_bytes=128,
        content_type="application/octet-stream",
        settings=_settings(),
    )
    assert result.extension == ".pt"
    assert result.original_filename == "model.pt"


def test_rejects_unsupported_extension() -> None:
    with pytest.raises(UploadValidationError) as exc:
        validate_upload_metadata(
            filename="notes.exe",
            size_bytes=10,
            content_type=None,
            settings=_settings(),
        )
    assert exc.value.code == "UNSUPPORTED_FILE_TYPE"


def test_rejects_oversized_file() -> None:
    settings = _settings(max_upload_size_mb=1)
    with pytest.raises(UploadValidationError) as exc:
        validate_upload_metadata(
            filename="big.pt",
            size_bytes=settings.max_upload_size_bytes + 1,
            content_type=None,
            settings=settings,
        )
    assert exc.value.code == "FILE_TOO_LARGE"


def test_strips_path_components_from_filename() -> None:
    result = validate_upload_metadata(
        filename="../evil/../../model.onnx",
        size_bytes=1,
        content_type=None,
        settings=_settings(),
    )
    assert result.original_filename == "model.onnx"
    assert result.extension == ".onnx"


def test_rejects_missing_filename() -> None:
    with pytest.raises(UploadValidationError) as exc:
        validate_upload_metadata(
            filename=None,
            size_bytes=0,
            content_type=None,
            settings=_settings(),
        )
    assert exc.value.code == "INVALID_FILENAME"
