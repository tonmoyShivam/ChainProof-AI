"""Minimal persistence for confirmed blockchain registrations (Milestone 4)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelRegistration(Base):
    __tablename__ = "model_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(66), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    version_label: Mapped[str] = mapped_column(String(64), default="1", nullable=False)
    on_chain_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    parent_model_id: Mapped[str | None] = mapped_column(String(66), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    artifact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    creator_wallet: Mapped[str] = mapped_column(String(42), nullable=False)
    contract_address: Mapped[str] = mapped_column(String(42), nullable=False)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(66), nullable=False, index=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)
    registration_status: Mapped[str] = mapped_column(String(32), nullable=False, default="confirmed")
    framework: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    framework_version: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
