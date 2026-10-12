import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.services.auth_service import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.get("/providers")
def providers():
    return {"google": bool(settings.google_client_id and settings.google_client_secret)}


@router.get("/google")
def google_start():
    if not providers()["google"]:
        raise HTTPException(503, "Google sign-in is not configured.")
    state = secrets.token_urlsafe(32)
    params = {"client_id": settings.google_client_id, "redirect_uri": callback_url(),
              "response_type": "code", "scope": "openid email", "state": state, "prompt": "select_account"}
    response = RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))
    response.set_cookie("google_oauth_state", state, httponly=True, samesite="lax", max_age=600,
                        secure=settings.verification_base_url.startswith("https://"))
    return response


def callback_url():
    return settings.verification_base_url.rstrip("/") + "/api/v1/auth/google/callback"


@router.get("/google/callback")
def google_callback(request: Request, state: str = "", code: str = "", db: Session = Depends(get_db)):
    expected = request.cookies.get("google_oauth_state", "")
    if not expected or not state or not secrets.compare_digest(state, expected) or not code:
        raise HTTPException(400, "Google sign-in was cancelled or expired. Please try again.")
    if not providers()["google"]:
        raise HTTPException(503, "Google sign-in is not configured.")
    try:
        with httpx.Client(timeout=15) as client:
            token = client.post("https://oauth2.googleapis.com/token", data={"code": code,
                "client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
                "redirect_uri": callback_url(), "grant_type": "authorization_code"})
            token.raise_for_status()
            info = client.get("https://openidconnect.googleapis.com/v1/userinfo",
                              headers={"Authorization": "Bearer " + token.json()["access_token"]})
            info.raise_for_status()
            identity = info.json()
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(400, "Google sign-in failed. Please try again.")
    # Google is authoritative for Gmail and verified Workspace addresses only.
    email = str(identity.get("email", "")).strip().lower()
    if identity.get("email_verified") is not True or not identity.get("sub") or not email:
        raise HTTPException(403, "A verified Google email is required.")
    user = db.query(User).filter_by(email=email).first()
    if user and not (email.endswith("@gmail.com") or identity.get("hd")):
        raise HTTPException(409, "Please use the email link to sign in to this existing account.")
    if user is None:
        user = User(email=email, email_verified=True, is_active=True, is_admin=False)
        db.add(user)
        db.flush()
    if not user.is_active:
        raise HTTPException(403, "This account is inactive.")
    user.email_verified = True
    db.commit()
    response = RedirectResponse("/?signed_in=1", status_code=303)
    response.delete_cookie("google_oauth_state")
    response.set_cookie("access_token", create_access_token(user.id), httponly=True, samesite="lax",
                        secure=settings.verification_base_url.startswith("https://"), max_age=settings.jwt_expire_minutes * 60)
    return response
