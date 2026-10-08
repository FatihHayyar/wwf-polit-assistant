"""add text sync fingerprint

Revision ID: e808b0248330
Revises: 71604c45be20
Create Date: 2026-10-08 13:52:50.918222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e808b0248330'
down_revision: Union[str, Sequence[str], None] = '71604c45be20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "texts",
        sa.Column(
            "sync_fingerprint",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "texts",
        "sync_fingerprint",
    )