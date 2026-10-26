"""Pydantic schemas for health endpoints."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    environment: str


class BlockchainHealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    connected: bool
    rpc_url: str
    chain_id: Optional[int] = None
    latest_block: Optional[int] = None
    expected_chain_id: Optional[int] = None
    detail: str = Field(description="Human-readable connectivity status")
