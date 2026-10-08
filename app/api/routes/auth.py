
from __future__ import annotations

from html import escape

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin, get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.auth_service import create_access_token
from app.services.email_service import send_email
from app.services.email_verification_service import (
    create_login_token,
    create_verification_token,
    verify_email_token,
    verify_login_token,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Auth"],
)


class LoginRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
    message: str


def authentication_result_page(
    *,
    title: str,
    message: str,
    access_token: str | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    token_section = ""

    if access_token is not None:
        token_section = f"""
            <h2>Access Token</h2>
            <textarea
                style="width: 700px; max-width: 95%; height: 150px;"
                readonly
            >{escape(access_token)}</textarea>
            <p>
                Copy this token and use it in Swagger
                for authenticated endpoint testing.
            </p>
        """

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html lang="de">
            <head>
                <meta charset="UTF-8">
                <title>WWF Polit-Assistant</title>
            </head>
            <body>
                <h1>{escape(title)}</h1>
                <p>{escape(message)}</p>
                {token_section}
            </body>
        </html>
        """,
        status_code=status_code,
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    email = str(payload.email).strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is not None and user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already registered.",
        )

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

    raw_token = create_verification_token(
        db,
        user_id=user.id,
    )

    verification_url = (
        f"{settings.verification_base_url}"
        f"/api/v1/auth/verify-email"
        f"?token={raw_token}"
    )

    send_email(
        recipient=user.email,
        subject="WWF Polit-Assistant – E-Mail bestätigen",
        body=(
            "Hallo,\n\n"
            "bitte bestätige deine E-Mail-Adresse "
            "über folgenden Link:\n\n"
            f"{verification_url}\n\n"
            "Der Link ist nur für begrenzte Zeit gültig "
            "und kann nur einmal verwendet werden.\n\n"
            "Beste Grüsse\n"
            "WWF Polit-Assistant"
        ),
    )

    return RegisterResponse(
        message="A verification email has been sent.",
    )


@router.get(
    "/verify-email",
    response_class=HTMLResponse,
)
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    user_id = verify_email_token(
        db,
        raw_token=token,
    )

    if user_id is None:
        return authentication_result_page(
            title="Verification failed",
            message="The verification link is invalid or expired.",
            status_code=400,
        )

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        return authentication_result_page(
            title="Verification failed",
            message="User not found or inactive.",
            status_code=400,
        )

    user.email_verified = True
    db.commit()

    access_token = create_access_token(user.id)

    return authentication_result_page(
        title="Successfully verified",
        message="Your email address has been verified successfully.",
        access_token=access_token,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    email = str(payload.email).strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This email address is not registered.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please complete registration.",
        )

    raw_token = create_login_token(
        db,
        user_id=user.id,
    )

    login_url = (
        f"{settings.verification_base_url}"
        f"/api/v1/auth/verify-login"
        f"?token={raw_token}"
    )

    send_email(
        recipient=user.email,
        subject="WWF Polit-Assistant – Anmelden",
        body=(
            "Hallo,\n\n"
            "du hast einen Anmeldelink für "
            "WWF Polit-Assistant angefordert.\n\n"
            "Klicke auf den folgenden Link, "
            "um dich anzumelden:\n\n"
            f"{login_url}\n\n"
            "Der Link ist nur für begrenzte Zeit gültig "
            "und kann nur einmal verwendet werden.\n\n"
            "Falls du diese Anmeldung nicht angefordert hast, "
            "kannst du diese E-Mail ignorieren.\n\n"
            "Beste Grüsse\n"
            "WWF Polit-Assistant"
        ),
    )

    return LoginResponse(
        message="A login email has been sent.",
    )


@router.get(
    "/verify-login",
    response_class=HTMLResponse,
)
def verify_login(
    token: str,
    db: Session = Depends(get_db),
):
    user_id = verify_login_token(
        db,
        raw_token=token,
    )

    if user_id is None:
        return authentication_result_page(
            title="Login failed",
            message="The login link is invalid, expired or already used.",
            status_code=400,
        )

    user = db.get(User, user_id)

    if (
        user is None
        or not user.is_active
        or not user.email_verified
    ):
        return authentication_result_page(
            title="Login failed",
            message="This account cannot be used for login.",
            status_code=403,
        )

    access_token = create_access_token(user.id)

    return authentication_result_page(
        title="Successfully logged in",
        message="You have successfully signed in.",
        access_token=access_token,
    )


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
