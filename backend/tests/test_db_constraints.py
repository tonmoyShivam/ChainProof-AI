"""Database constraint tests for Milestone 5 schema."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.db import get_engine, init_db
from app.models.model import Model
from app.models.model_version import ModelVersion
from app.models.user import User
from app.repositories import users as users_repo
from sqlalchemy.orm import Session


def test_unique_email_and_version_constraints(tmp_env, client) -> None:
    _ = client  # ensures app/lifespan initialized schema
    engine = get_engine()
    init_db()
    with Session(engine) as session:
        users_repo.create_user(
            session,
            email="unique@example.com",
            password_hash=hash_password("password123"),
            display_name="A",
        )
        session.commit()

    with Session(engine) as session:
        with pytest.raises(IntegrityError):
            users_repo.create_user(
                session,
                email="unique@example.com",
                password_hash=hash_password("password123"),
                display_name="B",
            )
            session.commit()
        session.rollback()

    with Session(engine) as session:
        user = users_repo.get_by_email(session, "unique@example.com")
        assert user is not None
        family = Model(
            model_id="0x" + "ab" * 32,
            name="m",
            description="",
            creator_user_id=user.id,
            creator_wallet="0x" + "11" * 20,
            current_version=1,
        )
        session.add(family)
        session.flush()
        v1 = ModelVersion(
            model_family_id=family.id,
            on_chain_model_id="0x" + "cd" * 32,
            version_number=1,
            sha256_hash="a" * 64,
            metadata_hash="b" * 64,
            storage_path="artifacts/x.pt",
            contract_address="0x" + "22" * 20,
            chain_id=31337,
            transaction_hash="0x" + "33" * 32,
            block_number=1,
            registration_status="confirmed",
        )
        session.add(v1)
        session.commit()

        with pytest.raises(IntegrityError):
            session.add(
                ModelVersion(
                    model_family_id=family.id,
                    on_chain_model_id="0x" + "ef" * 32,
                    version_number=1,
                    sha256_hash="c" * 64,
                    metadata_hash="d" * 64,
                    storage_path="artifacts/y.pt",
                    contract_address="0x" + "22" * 20,
                    chain_id=31337,
                    transaction_hash="0x" + "44" * 32,
                    block_number=2,
                    registration_status="confirmed",
                )
            )
            session.commit()
