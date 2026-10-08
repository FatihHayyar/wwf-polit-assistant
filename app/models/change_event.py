
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ChangeEvent(Base):
    __tablename__ = "change_events"
    __table_args__ = (
        UniqueConstraint(
            "dataset",
            "source_id",
            "change_type",
            "fingerprint",
            name="uq_change_events_source_version",
        ),
        Index(
            "idx_change_events_affair_id",
            "affair_id",
        ),
        Index(
            "idx_change_events_detected_at",
            "detected_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    dataset: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    affair_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    change_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
