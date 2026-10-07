"""add classification concept code

Revision ID: 097d34b2933a
Revises: 30d26c97d0dd
Create Date: 2026-10-07 19:56:36.892419
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "097d34b2933a"
down_revision: Union[str, Sequence[str], None] = "30d26c97d0dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing rules belong to the old classification model and do not
    # have semantic concept codes. No Affair classifications/evidence
    # have been persisted yet, so they can safely be rebuilt by the
    # classification seed after this migration.
    op.execute("DELETE FROM classification_rules")

    op.add_column(
        "classification_rules",
        sa.Column(
            "concept_code",
            sa.String(length=150),
            nullable=False,
        ),
    )

    op.create_index(
        "idx_classification_rules_concept_code",
        "classification_rules",
        ["concept_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_classification_rules_concept_code",
        table_name="classification_rules",
    )

    op.drop_column(
        "classification_rules",
        "concept_code",
    )