"""Model version ORM model (one on-chain registration per version)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class ModelVersion(Base):
    __tablename__ = "model_versions"
    __table_args__ = (
        UniqueConstraint("model_family_id", "version_number", name="uq_model_version_number"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    # FK to models.id (family row), not the on-chain bytes32 model_id.
    model_family_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # On-chain bytes32 id for THIS version record (unique per registration).
    on_chain_model_id: Mapped[str] = mapped_column(String(66), unique=True, index=True, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metadata_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    framework: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    framework_version: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    architecture: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_type: Mapped[str] = mapped_column(String(32), nullable=False, default="local")
    contract_address: Mapped[str] = mapped_column(String(42), nullable=False)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_hash: Mapped[str] = mapped_column(String(66), nullable=False, index=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False)
    registration_status: Mapped[str] = mapped_column(String(32), nullable=False, default="confirmed")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    model = relationship("Model", back_populates="versions")
    parent_version = relationship("ModelVersion", remote_side=[id], uselist=False)
    verification_logs = relationship(
        "VerificationLog", back_populates="model_version", cascade="all, delete-orphan"
    )
