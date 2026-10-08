"""add sync checkpoints

Revision ID: 3ce7689cb852
Revises: e8e80da6c31b
Create Date: 2026-10-08 13:00:51.115271

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ce7689cb852'
down_revision: Union[str, Sequence[str], None] = 'e8e80da6c31b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
