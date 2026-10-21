"""Named subscription profiles.

A user can keep several independent filter combinations, e.g. "Energie in
Bern" and "Biodiversität in Zürich". Within a profile, values of one filter are
alternatives; different filters must all match. A profile without topics,
cantons, keywords and affair types is paused.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

MAX_PROFILES_PER_USER = 10


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionProfile(Base):
    __tablename__ = "subscription_profiles"
    __table_args__ = (Index("idx_subscription_profiles_user_id", "user_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    # Category IDs include parents; a parent covers all of its subcategories.
    category_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    canton_keys: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # Empty means all nine datasets.
    datasets: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    # Harmonised German affair types, e.g. "Motion" or "Interpellation".
    affair_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now,
    )

    @property
    def has_filters(self) -> bool:
        return bool(self.category_ids or self.canton_keys or self.keywords or self.affair_types)
