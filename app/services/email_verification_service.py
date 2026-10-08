
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.email_token import EmailToken


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _create_email_token(
    db: Session,
    *,
    user_id: int,
    purpose: str,
) -> str:
    db.execute(
        delete(EmailToken).where(
            EmailToken.user_id == user_id,
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
        )
    )

    raw_token = secrets.token_urlsafe(48)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = utc_now() + timedelta(
        minutes=settings.email_verification_minutes
    )

    token = EmailToken(
        user_id=user_id,
        token_hash=token_hash,
        purpose=purpose,
        expires_at=expires_at,
    )

    db.add(token)
    db.commit()

    return raw_token


def _consume_email_token(
    db: Session,
    *,
    raw_token: str,
    purpose: str,
) -> int | None:
    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    token = (
        db.query(EmailToken)
        .filter(
            EmailToken.token_hash == token_hash,
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
        )
        .with_for_update()
        .first()
    )

    if token is None:
        return None

    expires_at = token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= utc_now():
        return None

    token.used_at = utc_now()
    db.commit()

    return token.user_id


def create_verification_token(
    db: Session,
    *,
    user_id: int,
) -> str:
    return _create_email_token(
        db,
        user_id=user_id,
        purpose="verify_email",
    )


def verify_email_token(
    db: Session,
    *,
    raw_token: str,
) -> int | None:
    return _consume_email_token(
        db,
        raw_token=raw_token,
        purpose="verify_email",
    )


def create_login_token(
    db: Session,
    *,
    user_id: int,
) -> str:
    return _create_email_token(
        db,
        user_id=user_id,
        purpose="login",
    )


def verify_login_token(
    db: Session,
    *,
    raw_token: str,
) -> int | None:
    return _consume_email_token(
        db,
        raw_token=raw_token,
        purpose="login",
    )
