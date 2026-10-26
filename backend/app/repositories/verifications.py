"""Verification log repository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.verification_log import VerificationLog


def add_log(session: Session, log: VerificationLog) -> VerificationLog:
    session.add(log)
    session.flush()
    return log


def list_for_model_id(session: Session, model_id: str, *, limit: int = 100) -> list[VerificationLog]:
    stmt = (
        select(VerificationLog)
        .where(VerificationLog.requested_model_id == model_id)
        .order_by(VerificationLog.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def count_by_result(session: Session, result: str) -> int:
    stmt = select(func.count()).select_from(VerificationLog).where(VerificationLog.result == result)
    return int(session.scalar(stmt) or 0)


def count_all(session: Session) -> int:
    stmt = select(func.count()).select_from(VerificationLog)
    return int(session.scalar(stmt) or 0)
