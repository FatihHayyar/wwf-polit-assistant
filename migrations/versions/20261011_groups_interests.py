"""Register group/interest synchronization and index meeting group relationships."""
from alembic import op

revision = "20261011_groups_interests"
down_revision = "20261011_keywords_watches"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_meetings_group_id", "meetings", ["group_id"])
    op.execute("INSERT INTO sync_checkpoints (dataset, status) VALUES ('groups', 'idle'), ('interests', 'idle') ON CONFLICT (dataset) DO NOTHING")


def downgrade():
    op.drop_index("idx_meetings_group_id", table_name="meetings")
    op.execute("DELETE FROM sync_checkpoints WHERE dataset IN ('groups', 'interests')")
