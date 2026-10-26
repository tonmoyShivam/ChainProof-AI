"""Dashboard statistics and recent activity (real DB aggregates only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db import get_session
from app.models.model import Model
from app.models.model_version import ModelVersion
from app.models.user import User
from app.repositories import verifications as verifications_repo
from app.schemas.dashboard import DashboardStatsResponse, RecentActivityItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def dashboard_stats(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
) -> DashboardStatsResponse:
    total_models = int(session.scalar(select(func.count()).select_from(Model)) or 0)
    return DashboardStatsResponse(
        total_registered_models=total_models,
        total_verification_attempts=verifications_repo.count_all(session),
        successful_verifications=verifications_repo.count_by_result(session, "VERIFIED"),
        integrity_mismatches=verifications_repo.count_by_result(session, "INTEGRITY_MISMATCH"),
    )


@router.get("/recent-activity", response_model=list[RecentActivityItem])
def recent_activity(
    session: Session = Depends(get_session),
    _user: User = Depends(get_current_user),
    limit: int = 20,
) -> list[RecentActivityItem]:
    limit = max(1, min(limit, 100))
    stmt = (
        select(ModelVersion, Model)
        .join(Model, ModelVersion.model_family_id == Model.id)
        .order_by(ModelVersion.registered_at.desc())
        .limit(limit)
    )
    rows = session.execute(stmt).all()
    return [
        RecentActivityItem(
            model_id=version.on_chain_model_id,
            name=family.name,
            version=version.version_number,
            registration_time=version.registered_at,
            creator=family.creator_wallet or family.creator_user_id,
            status=version.registration_status,
            transaction_hash=version.transaction_hash,
        )
        for version, family in rows
    ]
