
"""allow passwordless user registration

Revision ID: d07880fadf21
Revises: cbc541a52a97
Create Date: 2026-10-08 15:58:31.139582
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d07880fadf21"
down_revision: Union[str, Sequence[str], None] = "cbc541a52a97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow users to register without a password."""
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    """Restore the password requirement."""
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
