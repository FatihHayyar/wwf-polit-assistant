"""add sync checkpoints

Revision ID: 9148dc863794
Revises: 3ce7689cb852
Create Date: 2026-10-08 13:01:57.189476

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9148dc863794"
down_revision: Union[str, Sequence[str], None] = "3ce7689cb852"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sync_checkpoints",
        sa.Column(
            "dataset",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "last_updated_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "last_id",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "last_run_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="idle",
        ),
        sa.Column(
            "records_processed",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "records_new",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "records_changed",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "records_unchanged",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "records_error",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("dataset"),
    )


def downgrade() -> None:
    op.drop_table("sync_checkpoints")