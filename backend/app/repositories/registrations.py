"""Persistence helpers for model registration records."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.registration import ModelRegistration


def get_by_model_id(session: Session, model_id: str) -> ModelRegistration | None:
    stmt = select(ModelRegistration).where(ModelRegistration.model_id == model_id)
    return session.scalar(stmt)


def list_registrations(session: Session, *, limit: int = 50) -> list[ModelRegistration]:
    stmt = (
        select(ModelRegistration)
        .order_by(ModelRegistration.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def add_registration(session: Session, record: ModelRegistration) -> ModelRegistration:
    session.add(record)
    session.flush()
    return record
