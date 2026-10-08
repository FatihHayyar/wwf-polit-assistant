
"""add user subscriptions and notifications

Revision ID: cbc541a52a97
Revises: e808b0248330
Create Date: 2026-10-08 15:51:20.870685
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "cbc541a52a97"
down_revision: Union[str, Sequence[str], None] = "e808b0248330"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create only the five new application tables."""

    op.create_table(
        "change_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("dataset", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("affair_id", sa.BigInteger(), nullable=True),
        sa.Column("change_type", sa.String(length=20), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dataset",
            "source_id",
            "change_type",
            "fingerprint",
            name="uq_change_events_source_version",
        ),
    )
    op.create_index(
        "idx_change_events_affair_id",
        "change_events",
        ["affair_id"],
    )
    op.create_index(
        "idx_change_events_detected_at",
        "change_events",
        ["detected_at"],
    )

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("change_event_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["change_event_id"],
            ["change_events.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "change_event_id",
            name="uq_notifications_user_change_event",
        ),
    )
    op.create_index(
        "idx_notifications_status",
        "notifications",
        ["status"],
    )
    op.create_index(
        "idx_notifications_user_created_at",
        "notifications",
        ["user_id", "created_at"],
    )

    op.create_table(
        "user_canton_subscriptions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("canton_key", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "canton_key",
            name="uq_user_canton_subscriptions",
        ),
    )
    op.create_index(
        "idx_user_canton_subscriptions_canton_key",
        "user_canton_subscriptions",
        ["canton_key"],
    )

    op.create_table(
        "user_category_subscriptions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["classification_categories.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "category_id",
            name="uq_user_category_subscriptions",
        ),
    )
    op.create_index(
        "idx_user_category_subscriptions_category_id",
        "user_category_subscriptions",
        ["category_id"],
    )


def downgrade() -> None:
    """Remove only the five tables introduced by this migration."""

    op.drop_index(
        "idx_user_category_subscriptions_category_id",
        table_name="user_category_subscriptions",
    )
    op.drop_table("user_category_subscriptions")

    op.drop_index(
        "idx_user_canton_subscriptions_canton_key",
        table_name="user_canton_subscriptions",
    )
    op.drop_table("user_canton_subscriptions")

    op.drop_index(
        "idx_notifications_user_created_at",
        table_name="notifications",
    )
    op.drop_index(
        "idx_notifications_status",
        table_name="notifications",
    )
    op.drop_table("notifications")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    op.drop_index(
        "idx_change_events_detected_at",
        table_name="change_events",
    )
    op.drop_index(
        "idx_change_events_affair_id",
        table_name="change_events",
    )
    op.drop_table("change_events")
