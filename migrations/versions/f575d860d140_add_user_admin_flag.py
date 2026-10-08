"""add user admin flag

Revision ID: f575d860d140
Revises: 5ceea5c9c5d9
Create Date: 2026-10-08 17:02:11.330173
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "f575d860d140"
down_revision: Union[str, Sequence[str], None] = "5ceea5c9c5d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add administrator flag to users."""
    op.add_column(
        "users",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove administrator flag from users."""
    op.drop_column("users", "is_admin")