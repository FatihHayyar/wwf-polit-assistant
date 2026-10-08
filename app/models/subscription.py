
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserCategorySubscription(Base):
    __tablename__ = "user_category_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category_id",
            name="uq_user_category_subscriptions",
        ),
        Index(
            "idx_user_category_subscriptions_category_id",
            "category_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "classification_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class UserCantonSubscription(Base):
    __tablename__ = "user_canton_subscriptions"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "canton_key",
            name="uq_user_canton_subscriptions",
        ),
        Index(
            "idx_user_canton_subscriptions_canton_key",
            "canton_key",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    canton_key: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
