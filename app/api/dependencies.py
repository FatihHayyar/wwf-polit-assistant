from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import decode_access_claims


bearer_scheme = HTTPBearer(auto_error=False)


def request_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    access_token: str | None = Cookie(default=None),
) -> str | None:
    # Swagger / API:
    # Authorization: Bearer <token>
    if credentials is not None:
        return credentials.credentials

    # Browser:
    # HttpOnly access_token cookie
    return access_token or None


def user_for_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None

    claims = decode_access_claims(token)

    if claims is None:
        return None

    user = db.get(User, claims.user_id)

    if (
        user is None
        or not user.is_active
        or user.session_version != claims.session_version
    ):
        return None

    return user


def get_current_user(
    token: str | None = Depends(request_token),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user = user_for_token(db, token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        )

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required.",
        )

    return current_user
