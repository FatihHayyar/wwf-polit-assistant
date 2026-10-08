
"""add email verification tokens

Revision ID: 5ceea5c9c5d9
Revises: d07880fadf21
Create Date: 2026-10-08 16:02:29.503239
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5ceea5c9c5d9"
down_revision: Union[str, Sequence[str], None] = "d07880fadf21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the email verification and login token table."""

    op.create_table(
        "email_tokens",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "purpose",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )

    op.create_index(
        "idx_email_tokens_expires_at",
        "email_tokens",
        ["expires_at"],
    )

    op.create_index(
        "idx_email_tokens_user_id",
        "email_tokens",
        ["user_id"],
    )


def downgrade() -> None:
    """Remove only the email token table."""

    op.drop_index(
        "idx_email_tokens_user_id",
        table_name="email_tokens",
    )

    op.drop_index(
        "idx_email_tokens_expires_at",
        table_name="email_tokens",
    )

    op.drop_table("email_tokens")
