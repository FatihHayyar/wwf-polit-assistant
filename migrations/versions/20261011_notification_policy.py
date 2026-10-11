"""Preserve before/after change evidence and notification policy decisions."""
from alembic import op
import sqlalchemy as sa

revision = "20261011_notification_policy"
down_revision = "20261011_groups_interests"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("change_events", sa.Column("changes", sa.JSON(), nullable=True))
    op.add_column("change_events", sa.Column("notification_eligible", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("change_events", sa.Column("notification_policy", sa.String(50), nullable=True))


def downgrade():
    op.drop_column("change_events", "notification_policy")
    op.drop_column("change_events", "notification_eligible")
    op.drop_column("change_events", "changes")
