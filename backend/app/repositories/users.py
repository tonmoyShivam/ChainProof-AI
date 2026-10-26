"""User repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(session: Session, user_id: str) -> User | None:
    return session.get(User, user_id)


def get_by_email(session: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email.lower())
    return session.scalar(stmt)


def create_user(
    session: Session,
    *,
    email: str,
    password_hash: str,
    display_name: str,
    role: str = "user",
    wallet_address: str | None = None,
) -> User:
    user = User(
        email=email.lower().strip(),
        password_hash=password_hash,
        display_name=display_name.strip() or email.split("@")[0],
        role=role,
        wallet_address=wallet_address,
    )
    session.add(user)
    session.flush()
    return user
