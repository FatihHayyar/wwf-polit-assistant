from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user, request_token, user_for_token
from app.api.email_links import (
    confirmation_page,
    form_token,
    require_same_origin,
    result_page,
    set_session_cookie,
)
from app.core.config import settings
from app.core.rate_limit import (
    AUTH_EMAIL_COOLDOWN,
    AUTH_EMAIL_PER_ADDRESS,
    AUTH_EMAIL_PER_IP,
    TOKEN_CONFIRM_PER_IP,
    client_address,
    enforce,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.email_service import EmailServiceError, send_email
from app.services.email_verification_service import (
    create_login_token,
    create_verification_token,
    verify_email_token,
    verify_login_token,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)

# Register and login deliberately return the same answer whether or not an
# account exists, so the endpoints cannot be used to test email addresses.
LINK_SENT_MESSAGE = (
    "If this address can be used, a link has been sent to it."
)


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    message: str


def link_url(path: str, token: str) -> str:
    return f"{settings.verification_base_url.rstrip('/')}{path}?token={token}"


def deliver_email(recipient: str, subject: str, body: str) -> None:
    try:
        send_email(recipient=recipient, subject=subject, body=body)
    except EmailServiceError:
        logger.exception("Authentication email could not be sent.")


def queue_verification_email(background: BackgroundTasks, db: Session, user: User) -> None:
    token = create_verification_token(db, user_id=user.id)
    background.add_task(
        deliver_email,
        user.email,
        "WWF Polit-Assistant – E-Mail bestätigen",
        "Hallo,\n\n"
        "bitte bestätige deine E-Mail-Adresse "
        "über folgenden Link:\n\n"
        f"{link_url('/api/v1/auth/verify-email', token)}\n\n"
        "Der Link ist nur für begrenzte Zeit gültig "
        "und kann nur einmal verwendet werden.\n\n"
        "Falls du dich nicht registriert hast, "
        "kannst du diese E-Mail ignorieren.\n\n"
        "Beste Grüsse\n"
        "WWF Polit-Assistant",
    )


def queue_login_email(background: BackgroundTasks, db: Session, user: User) -> None:
    token = create_login_token(db, user_id=user.id)
    background.add_task(
        deliver_email,
        user.email,
        "WWF Polit-Assistant – Anmelden",
        "Hallo,\n\n"
        "du hast einen Anmeldelink für "
        "WWF Polit-Assistant angefordert.\n\n"
        "Klicke auf den folgenden Link, "
        "um dich anzumelden:\n\n"
        f"{link_url('/api/v1/auth/verify-login', token)}\n\n"
        "Der Link ist nur für begrenzte Zeit gültig "
        "und kann nur einmal verwendet werden.\n\n"
        "Falls du diese Anmeldung nicht angefordert hast, "
        "kannst du diese E-Mail ignorieren.\n\n"
        "Beste Grüsse\n"
        "WWF Polit-Assistant",
    )


def limit_email_request(request: Request, email: str) -> None:
    enforce(
        (f"auth-ip:{client_address(request)}", AUTH_EMAIL_PER_IP),
        (f"auth-cooldown:{email}", AUTH_EMAIL_COOLDOWN),
        (f"auth-address:{email}", AUTH_EMAIL_PER_ADDRESS),
    )


def find_user(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


@router.post(
    "/register",
    response_model=RegisterResponse,
)
def register(
    payload: RegisterRequest,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    email = str(payload.email).strip().lower()
    limit_email_request(request, email)

    user = find_user(db, email)

    if user is None:
        user = User(
            email=email,
            password_hash=None,
            is_active=True,
            email_verified=False,
            is_admin=False,
        )

        db.add(user)
        db.flush()

    if user.is_active and user.email_verified:
        # The owner of an existing account receives a sign-in link instead.
        queue_login_email(background, db, user)
    elif user.is_active:
        queue_verification_email(background, db, user)

    return RegisterResponse(message=LINK_SENT_MESSAGE)


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> LoginResponse:
    email = str(payload.email).strip().lower()
    limit_email_request(request, email)

    user = find_user(db, email)

    if user is not None and user.is_active:
        if user.email_verified:
            queue_login_email(background, db, user)
        else:
            queue_verification_email(background, db, user)

    return LoginResponse(message=LINK_SENT_MESSAGE)


@router.get(
    "/verify-email",
    response_class=HTMLResponse,
)
def verify_email_page(token: str) -> HTMLResponse:
    return confirmation_page(
        title="E-Mail-Adresse bestätigen",
        message="Bitte bestätige deine Registrierung. Danach bist du angemeldet.",
        button="Registrierung bestätigen",
        action="/api/v1/auth/verify-email",
        token=token,
    )


@router.post(
    "/verify-email",
    response_class=HTMLResponse,
)
async def verify_email(
    request: Request,
    db: Session = Depends(get_db),
):
    require_same_origin(request)
    enforce((f"token-ip:{client_address(request)}", TOKEN_CONFIRM_PER_IP))
    token = await form_token(request)

    user_id = verify_email_token(
        db,
        raw_token=token,
    )

    user = db.get(User, user_id) if user_id is not None else None

    if user is None or not user.is_active:
        return result_page(
            title="Bestätigung fehlgeschlagen",
            message="Der Bestätigungslink ist ungültig oder abgelaufen. Bitte fordere einen neuen Link an.",
            status_code=400,
        )

    user.email_verified = True
    db.commit()

    result = RedirectResponse("/?signed_in=1", status_code=303)
    set_session_cookie(result, user)
    return result


@router.get(
    "/verify-login",
    response_class=HTMLResponse,
)
def verify_login_page(token: str) -> HTMLResponse:
    return confirmation_page(
        title="Anmelden",
        message="Bitte bestätige die Anmeldung bei WWF Polit-Assistant.",
        button="Jetzt anmelden",
        action="/api/v1/auth/verify-login",
        token=token,
    )


@router.post(
    "/verify-login",
    response_class=HTMLResponse,
)
async def verify_login(
    request: Request,
    db: Session = Depends(get_db),
):
    require_same_origin(request)
    enforce((f"token-ip:{client_address(request)}", TOKEN_CONFIRM_PER_IP))
    token = await form_token(request)

    user_id = verify_login_token(
        db,
        raw_token=token,
    )

    user = db.get(User, user_id) if user_id is not None else None

    if (
        user is None
        or not user.is_active
        or not user.email_verified
    ):
        return result_page(
            title="Anmeldung fehlgeschlagen",
            message="Der Anmeldelink ist ungültig, abgelaufen oder wurde bereits verwendet.",
            status_code=400,
        )

    result = RedirectResponse("/?signed_in=1", status_code=303)
    set_session_cookie(result, user)
    return result


@router.get("/me")
def my_account(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "email_verified": current_user.email_verified}


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    token: str | None = Depends(request_token),
    db: Session = Depends(get_db),
):
    # Revoke every access token issued so far, not just this browser's cookie.
    user = user_for_token(db, token)
    if user is not None:
        user.session_version += 1
        db.commit()
    response.delete_cookie("access_token", path="/")


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.delete(current_user)
    db.commit()

    response.delete_cookie(
        key="access_token",
        path="/",
    )


@router.delete(
    "/admin/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    db.delete(user)
    db.commit()
