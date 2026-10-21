"""Demo endpoints; they exist only when DEMO_MODE is enabled."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.rate_limit import DEMO_NOTIFICATION_PER_USER, enforce
from app.db.database import get_db
from app.models.user import User
from app.services.demo_notification_service import (
    DemoNotificationError,
    create_demo_affair,
    demo_category_choices,
)
from app.services.email_service import EmailServiceError
from app.services.notification_email_service import send_pending_notifications


router = APIRouter(prefix="/api/v1/demo", tags=["Demo"])


class DemoStatus(BaseModel):
    enabled: bool
    mailbox_url: str | None = None


class DemoTopic(BaseModel):
    code: str
    name: str


class DemoTopics(BaseModel):
    topics: list[DemoTopic]
    preselected: str | None


class DemoNotificationRequest(BaseModel):
    category_code: str = Field(min_length=1, max_length=100)


class DemoNotificationResponse(BaseModel):
    affair_id: int
    title: str
    canton: str | None
    categories: list[str]
    notifications_for_user: int
    emails_sent: int
    emails_failed: int
    mailbox_url: str | None
    hints: list[str]


def require_demo_mode() -> None:
    if not settings.demo_mode:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")


@router.get("/status", response_model=DemoStatus)
def demo_status() -> DemoStatus:
    return DemoStatus(enabled=settings.demo_mode,
                      mailbox_url=settings.demo_mailbox_url if settings.demo_mode else None)


@router.get("/topics", response_model=DemoTopics, dependencies=[Depends(require_demo_mode)])
def demo_topics(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DemoTopics:
    topics, preselected = demo_category_choices(db, user)
    return DemoTopics(topics=[DemoTopic(**topic) for topic in topics], preselected=preselected)


@router.post("/notifications", response_model=DemoNotificationResponse,
             status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_demo_mode)])
def create_demo_notification(
    payload: DemoNotificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DemoNotificationResponse:
    enforce((f"demo-user:{user.id}", DEMO_NOTIFICATION_PER_USER))
    try:
        result = create_demo_affair(db, user, payload.category_code)
    except DemoNotificationError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    db.commit()

    if result.notifications_for_user:
        try:
            result.emails_sent, result.emails_failed = send_pending_notifications(user_id=user.id)
        except EmailServiceError as exc:
            result.emails_failed = max(result.emails_failed, 1)
            result.hints.append(f"Email delivery failed: {exc}")

    return DemoNotificationResponse(**vars(result), mailbox_url=settings.demo_mailbox_url)
