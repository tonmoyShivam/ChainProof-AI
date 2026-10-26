"""Schemas for model registration, history, and verification APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ModelVersionResponse(BaseModel):
    id: str
    on_chain_model_id: str
    version_number: int
    parent_version_id: Optional[str] = None
    sha256_hash: str
    metadata_hash: str
    framework: str = ""
    framework_version: str = ""
    architecture: str = ""
    storage_path: str
    storage_type: str = "local"
    contract_address: str
    chain_id: int
    transaction_hash: str
    block_number: int
    registration_status: str
    registered_at: datetime


class ModelRegistrationResponse(BaseModel):
    model_id: str
    name: str
    description: str
    version_label: str
    on_chain_version: int
    parent_model_id: Optional[str] = None
    sha256_hash: str
    metadata_hash: str
    storage_path: str
    creator_user_id: str
    creator_wallet: str
    contract_address: str
    chain_id: int
    transaction_hash: str
    block_number: int
    registration_status: Literal["confirmed"] = "confirmed"
    framework: str = ""
    framework_version: str = ""
    architecture: str = ""
    created_at: datetime


class ModelDetailResponse(BaseModel):
    model_id: str
    name: str
    description: str
    creator_user_id: str
    creator_wallet: str
    current_version: int
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[ModelVersionResponse] = None


class VerificationResponse(BaseModel):
    status: Literal[
        "VERIFIED",
        "INTEGRITY_MISMATCH",
        "MODEL_NOT_FOUND",
        "VERIFICATION_UNAVAILABLE",
    ]
    model_id: str
    expected_hash: Optional[str] = None
    actual_hash: Optional[str] = None
    detail: str
    creator_wallet: Optional[str] = None
    on_chain_version: Optional[int] = None


class VerificationLogResponse(BaseModel):
    id: str
    model_version_id: Optional[str] = None
    requested_model_id: str
    provided_hash: Optional[str] = None
    expected_hash: Optional[str] = None
    result: str
    error_code: Optional[str] = None
    created_at: datetime


class ErrorResponse(BaseModel):
    error_code: str
    detail: str = Field(description="Human-readable error detail")
