"""add sync checkpoints

Revision ID: e8e80da6c31b
Revises: 097d34b2933a
Create Date: 2026-10-08 13:00:32.646779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8e80da6c31b'
down_revision: Union[str, Sequence[str], None] = '097d34b2933a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
