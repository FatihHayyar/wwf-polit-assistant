"""Keyword filters and explicit record monitoring."""
from alembic import op
import sqlalchemy as sa

revision = "20261011_keywords_watches"
down_revision = "20261011_entity_monitoring"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("user_keyword_subscriptions",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("keyword", sa.String(200), primary_key=True))
    op.create_table("user_record_watches",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dataset", sa.String(50), primary_key=True),
        sa.Column("record_id", sa.BigInteger(), primary_key=True))


def downgrade():
    op.drop_table("user_record_watches")
    op.drop_table("user_keyword_subscriptions")
