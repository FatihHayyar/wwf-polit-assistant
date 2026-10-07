"""Baseline application schema.

The initial OpenParlData snapshot was imported and validated before
Alembic became the authoritative schema migration mechanism.

This revision therefore represents the already existing application
schema and intentionally performs no database changes.

Revision ID: c09225df3432
Revises:
Create Date: 2026-10-07
"""

from typing import Sequence, Union


revision: str = "c09225df3432"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Mark the existing application schema as the baseline."""
    pass


def downgrade() -> None:
    """The baseline does not remove the pre-existing application schema."""
    pass