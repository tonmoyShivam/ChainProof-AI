"""Model family and version repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.model import Model
from app.models.model_version import ModelVersion


def get_family_by_model_id(session: Session, model_id: str) -> Model | None:
    stmt = (
        select(Model)
        .options(selectinload(Model.versions))
        .where(Model.model_id == model_id)
    )
    return session.scalar(stmt)


def get_version_by_on_chain_id(session: Session, on_chain_model_id: str) -> ModelVersion | None:
    stmt = (
        select(ModelVersion)
        .options(selectinload(ModelVersion.model))
        .where(ModelVersion.on_chain_model_id == on_chain_model_id)
    )
    return session.scalar(stmt)


def resolve_family(session: Session, model_id: str) -> Model | None:
    family = get_family_by_model_id(session, model_id)
    if family is not None:
        return family
    version = get_version_by_on_chain_id(session, model_id)
    if version is None:
        return None
    return session.get(Model, version.model_family_id)


def list_families(session: Session, *, limit: int = 100) -> list[Model]:
    stmt = (
        select(Model)
        .options(selectinload(Model.versions))
        .order_by(Model.created_at.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt))


def add_family(session: Session, family: Model) -> Model:
    session.add(family)
    session.flush()
    return family


def add_version(session: Session, version: ModelVersion) -> ModelVersion:
    session.add(version)
    session.flush()
    return version


def list_versions_for_family(session: Session, family_id: str) -> list[ModelVersion]:
    stmt = (
        select(ModelVersion)
        .where(ModelVersion.model_family_id == family_id)
        .order_by(ModelVersion.version_number.asc())
    )
    return list(session.scalars(stmt))
