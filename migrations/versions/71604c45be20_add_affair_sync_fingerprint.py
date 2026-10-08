"""add affair sync fingerprint

Revision ID: 71604c45be20
Revises: 9148dc863794
Create Date: 2026-10-08 13:30:06.521975

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "71604c45be20"
down_revision: Union[str, Sequence[str], None] = "9148dc863794"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add fingerprint column used by incremental affair sync."""

    op.add_column(
        "affairs",
        sa.Column(
            "sync_fingerprint",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove affair sync fingerprint."""

    op.drop_column(
        "affairs",
        "sync_fingerprint",
    )