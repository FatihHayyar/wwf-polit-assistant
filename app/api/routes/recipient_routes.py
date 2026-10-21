import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.email_links import confirmation_page, form_token, require_same_origin, result_page
from app.core.config import settings
from app.core.rate_limit import RECIPIENT_UPDATE_PER_USER, TOKEN_CONFIRM_PER_IP, client_address, enforce
from app.db.database import get_db
from app.models.notification_recipient import NotificationRecipient
from app.models.user import User
from app.services.email_service import send_email

router = APIRouter(prefix="/api/v1/subscriptions/recipients", tags=["Subscriptions"])


class RecipientsUpdate(BaseModel):
    emails: list[EmailStr] = Field(min_length=1, max_length=10)


@router.get("")
def recipients(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(NotificationRecipient).filter_by(user_id=user.id).all()
    return [{"email": row.email, "verified": row.verified} for row in rows] or [{"email": user.email, "verified": True}]


@router.put("")
def update_recipients(payload: RecipientsUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    enforce((f"recipients-user:{user.id}", RECIPIENT_UPDATE_PER_USER))
    addresses = {str(email).strip().lower() for email in payload.emails}
    existing = {row.email: row for row in db.query(NotificationRecipient).filter_by(user_id=user.id)}
    for address, row in existing.items():
        if address not in addresses:
            db.delete(row)
    for address in addresses:
        if address in existing and existing[address].verified:
            continue
        row = existing.get(address) or NotificationRecipient(user_id=user.id, email=address, verified=address == user.email)
        if row.expires_at and row.expires_at.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            continue
        if not row.verified:
            token = secrets.token_urlsafe(48)
            row.token_hash = hashlib.sha256(token.encode()).hexdigest()
            row.expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.email_verification_minutes)
            send_email(recipient=address, subject="WWF: Benachrichtigungsadresse bestätigen",
                       body="Bitte bestätige diese Adresse für Benachrichtigungen:\n\n"
                       + settings.verification_base_url.rstrip("/") + "/api/v1/subscriptions/recipients/verify?token=" + token)
        db.add(row)
    db.commit()
    return recipients(user, db)


@router.get("/verify", response_class=HTMLResponse)
def verify_recipient_page(token: str):
    return confirmation_page(
        title="Benachrichtigungsadresse bestätigen",
        message="Bitte bestätige, dass Benachrichtigungen des WWF Polit-Assistant an diese Adresse gesendet werden dürfen.",
        button="Adresse bestätigen",
        action="/api/v1/subscriptions/recipients/verify",
        token=token,
    )


@router.post("/verify", response_class=HTMLResponse)
async def verify_recipient(request: Request, db: Session = Depends(get_db)):
    require_same_origin(request)
    enforce((f"token-ip:{client_address(request)}", TOKEN_CONFIRM_PER_IP))
    token = await form_token(request)
    row = db.query(NotificationRecipient).filter_by(token_hash=hashlib.sha256(token.encode()).hexdigest()).with_for_update().first()
    if row is None or row.expires_at is None or row.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        return result_page(title="Bestätigung fehlgeschlagen",
                           message="Dieser Bestätigungslink ist ungültig oder abgelaufen.", status_code=400)
    row.verified = True
    row.token_hash = None
    row.expires_at = None
    db.commit()
    return RedirectResponse("/?recipient_verified=1", status_code=303)
