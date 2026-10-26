"""Pydantic schemas for hashing and upload endpoints."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HashResponse(BaseModel):
    algorithm: Literal["sha256"] = "sha256"
    sha256_hex: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)
    filename: str


class UploadStoreResponse(BaseModel):
    artifact_id: str
    algorithm: Literal["sha256"] = "sha256"
    sha256_hex: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)
    original_filename: str
    stored_relative_path: str
    content_type: Optional[str] = None


class ErrorResponse(BaseModel):
    error_code: str
    detail: str
