"""Schemas for model registration and verification APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


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
    creator_wallet: str
    contract_address: str
    chain_id: int
    transaction_hash: str
    block_number: int
    registration_status: Literal["confirmed"] = "confirmed"
    framework: str = ""
    framework_version: str = ""
    created_at: datetime


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


class ErrorResponse(BaseModel):
    error_code: str
    detail: str = Field(description="Human-readable error detail")
