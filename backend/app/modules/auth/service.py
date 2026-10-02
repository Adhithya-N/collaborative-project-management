"""Business logic for registration and login - routers stay thin and call these functions."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.users.models import User


def register_user(db: Session, data: RegisterRequest) -> User:
    """Creates a new user account, rejecting duplicate emails."""
    existing = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()
    if existing is not None:
        # 409 Conflict - the request is well-formed but clashes with existing data.
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, data: LoginRequest) -> str:
    """Verifies credentials and returns a signed JWT access token."""
    user = db.execute(select(User).where(User.email == data.email)).scalar_one_or_none()

    # Same error for "no such user" and "wrong password" - avoids revealing which emails are registered.
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return create_access_token(subject=str(user.id))
