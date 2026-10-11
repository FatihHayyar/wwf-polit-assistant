"""Related affair monitoring and optional dataset subscriptions."""
from alembic import op
import sqlalchemy as sa

revision = "20261011_entity_monitoring"
down_revision = "f575d860d140"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "entity_classifications",
        sa.Column("dataset", sa.String(50), primary_key=True),
        sa.Column("entity_id", sa.BigInteger(), primary_key=True),
        sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("classification_categories.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.String(20), nullable=False),
        sa.Column("classifier_version", sa.String(50), nullable=False),
    )
    op.create_table(
        "change_event_affairs",
        sa.Column("change_event_id", sa.BigInteger(), sa.ForeignKey("change_events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("affair_id", sa.BigInteger(), primary_key=True),
    )
    op.create_index("ix_change_event_affairs_affair_id", "change_event_affairs", ["affair_id"])
    op.execute("INSERT INTO change_event_affairs (change_event_id, affair_id) SELECT id, affair_id FROM change_events WHERE affair_id IS NOT NULL")
    op.create_table(
        "user_dataset_subscriptions",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dataset", sa.String(50), primary_key=True),
    )


def downgrade():
    op.drop_table("entity_classifications")
    op.drop_table("user_dataset_subscriptions")
    op.drop_index("ix_change_event_affairs_affair_id", table_name="change_event_affairs")
    op.drop_table("change_event_affairs")
