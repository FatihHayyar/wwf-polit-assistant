"""Shared helpers for one-time links sent by email.

Opening a link (GET) only renders a confirmation page. The token is consumed by
the POST from that page, so link scanners in corporate mail systems that
prefetch URLs cannot use up a login or verification token.
"""
from __future__ import annotations

from html import escape
from urllib.parse import parse_qs, urlsplit

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.models.user import User
from app.services.auth_service import create_access_token


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="referrer" content="same-origin">
<title>WWF Polit-Assistant</title>
<link rel="stylesheet" href="/assets/style.css">
</head>
<body class="link-page">
<main class="link-card">
<p class="eyebrow">WWF Polit-Assistant</p>
<h1>{title}</h1>
<p>{message}</p>
{content}
</main>
</body>
</html>"""


def result_page(*, title: str, message: str, status_code: int = 200, home_link: bool = True) -> HTMLResponse:
    content = '<p><a href="/">Zur Anwendung</a></p>' if home_link else ""
    return HTMLResponse(
        PAGE_TEMPLATE.format(title=escape(title), message=escape(message), content=content),
        status_code=status_code,
    )


def confirmation_page(*, title: str, message: str, button: str, action: str, token: str) -> HTMLResponse:
    form = (
        f'<form method="post" action="{escape(action)}">'
        f'<input type="hidden" name="token" value="{escape(token)}">'
        f'<button class="primary" type="submit">{escape(button)}</button>'
        "</form>"
    )
    return HTMLResponse(PAGE_TEMPLATE.format(title=escape(title), message=escape(message), content=form))


def _origin(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}".lower()


def require_same_origin(request: Request) -> None:
    """Reject cross-site form posts, e.g. login CSRF with an attacker's token."""
    origin = request.headers.get("origin")
    if origin is None:
        # Non-browser clients do not send Origin; they cannot be used for CSRF.
        return
    allowed = {_origin(settings.verification_base_url), _origin(str(request.base_url))}
    if origin.lower() not in allowed:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cross-site request rejected.")


async def form_token(request: Request) -> str:
    """Read the token from an urlencoded form without python-multipart."""
    body = (await request.body())[:4096].decode("utf-8", errors="replace")
    token = parse_qs(body).get("token", [""])[0].strip()
    if not token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing token.")
    return token


def set_session_cookie(response: Response, user: User) -> None:
    response.set_cookie(
        "access_token",
        create_access_token(user.id, user.session_version),
        httponly=True,
        samesite="lax",
        secure=settings.verification_base_url.startswith("https://"),
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )
