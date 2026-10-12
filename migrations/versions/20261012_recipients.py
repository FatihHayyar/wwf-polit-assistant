"""Verified notification destinations, separate from the login account."""
from alembic import op
import sqlalchemy as sa

revision = "20261012_recipients"
down_revision = "20261011_unified_search"


def upgrade():
    # The additive table can be prepared while concurrent search indexes build.
    if sa.inspect(op.get_bind()).has_table("notification_recipients"):
        return
    op.create_table("notification_recipients",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("email", sa.String(320), primary_key=True),
        sa.Column("verified", sa.Boolean(), nullable=False),
        sa.Column("token_hash", sa.String(64), unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True)))


def downgrade():
    op.drop_table("notification_recipients")
