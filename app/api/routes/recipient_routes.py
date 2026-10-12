import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
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


@router.get("/verify")
def verify_recipient(token: str, db: Session = Depends(get_db)):
    row = db.query(NotificationRecipient).filter_by(token_hash=hashlib.sha256(token.encode()).hexdigest()).with_for_update().first()
    if row is None or row.expires_at is None or row.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(400, "This verification link is invalid or expired.")
    row.verified = True
    row.token_hash = None
    row.expires_at = None
    db.commit()
    return RedirectResponse("/?recipient_verified=1", status_code=303)
