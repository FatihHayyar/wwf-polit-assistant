from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


@dataclass(frozen=True)
class AccessClaims:
    user_id: int
    session_version: int


def create_access_token(user_id: int, session_version: int = 0) -> str:
    now = datetime.now(timezone.utc)

    expires_at = now + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "sv": session_version,
        "iat": now,
        "exp": expires_at,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_claims(token: str) -> AccessClaims | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")

        if user_id is None:
            return None

        # Tokens issued before session versions existed count as version 0.
        return AccessClaims(int(user_id), int(payload.get("sv", 0)))

    except (jwt.InvalidTokenError, ValueError, TypeError):
        return None


def decode_access_token(token: str) -> int | None:
    claims = decode_access_claims(token)
    return claims.user_id if claims else None
