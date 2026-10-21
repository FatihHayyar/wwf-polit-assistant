"""Small in-process rate limiter for endpoints that send email or accept tokens.

The limiter keeps sliding windows in memory. That is sufficient for the single
API process of the MVP; several API replicas would need a shared store such as
Redis so that limits apply across processes.
"""
from __future__ import annotations

import math
import threading
import time
from collections import deque
from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.core.config import settings


@dataclass(frozen=True)
class Limit:
    requests: int
    seconds: int


# Requests per client address, independent of the submitted email address.
AUTH_EMAIL_PER_IP = Limit(10, 15 * 60)
# Emails per target address; the first rule enforces a pause between emails.
AUTH_EMAIL_COOLDOWN = Limit(1, 60)
AUTH_EMAIL_PER_ADDRESS = Limit(5, 60 * 60)
TOKEN_CONFIRM_PER_IP = Limit(30, 15 * 60)
OAUTH_START_PER_IP = Limit(20, 15 * 60)
RECIPIENT_UPDATE_PER_USER = Limit(10, 60 * 60)
SUBSCRIPTION_CHANGE_PER_USER = Limit(60, 60 * 60)
DEMO_NOTIFICATION_PER_USER = Limit(5, 10 * 60)


class RateLimiter:
    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: Limit) -> float | None:
        """Record a request and return the seconds to wait if it is rejected."""
        now = self._clock()
        with self._lock:
            window = self._hits.setdefault(key, deque())
            while window and window[0] <= now - limit.seconds:
                window.popleft()
            if len(window) >= limit.requests:
                return window[0] + limit.seconds - now
            window.append(now)
            if len(self._hits) > 50_000:
                self._prune(now)
            return None

    def _prune(self, now: float) -> None:
        # No configured window is longer than one hour.
        for key in [key for key, hits in self._hits.items() if not hits or hits[-1] <= now - 3600]:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_address(request: Request) -> str:
    # Behind a reverse proxy, start uvicorn with --proxy-headers so that
    # request.client reflects the forwarded client address.
    return request.client.host if request.client else "unknown"


def enforce(*rules: tuple[str, Limit]) -> None:
    """Apply all rules; raise HTTP 429 when any of them is exhausted."""
    if not settings.rate_limit_enabled:
        return
    waits = [wait for key, limit in rules if (wait := limiter.hit(key, limit)) is not None]
    if waits:
        retry_after = max(1, math.ceil(max(waits)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(retry_after)},
        )
