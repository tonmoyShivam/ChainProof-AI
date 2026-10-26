"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db import get_session
from app.models.user import User
from app.repositories import users as users_repo
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        wallet_address=user.wallet_address,
        role=user.role,
        created_at=user.created_at,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    body: RegisterRequest,
    session: Session = Depends(get_session),
) -> UserResponse:
    if users_repo.get_by_email(session, body.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        user = users_repo.create_user(
            session,
            email=str(body.email),
            password_hash=hash_password(body.password),
            display_name=body.display_name,
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Email already registered") from exc
    return _user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(
    body: LoginRequest,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    user = users_repo.get_by_email(session, str(body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(
        subject=user.id,
        settings=settings,
        extra_claims={"role": user.role, "email": user.email},
    )
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(user: User = Depends(get_current_user)) -> MessageResponse:
    # Stateless JWT: client discards the token. Endpoint exists for API completeness
    # and to confirm the caller was authenticated.
    _ = user
    return MessageResponse(detail="Logged out")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(user)
