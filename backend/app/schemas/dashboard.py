"""Dashboard stats and activity schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_registered_models: int
    total_verification_attempts: int
    successful_verifications: int
    integrity_mismatches: int


class RecentActivityItem(BaseModel):
    model_id: str
    name: str
    version: int
    registration_time: datetime
    creator: str
    status: str
    transaction_hash: Optional[str] = None
