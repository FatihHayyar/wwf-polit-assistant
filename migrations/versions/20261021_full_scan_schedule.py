"""Remember the last complete comparison of each dataset.

Until this revision, agendas, votings, events, texts, groups and interests were
compared completely on every successful run, and affairs/meetings fell back to
a complete comparison whenever counts differed. Their last successful run is
therefore a valid starting value for the new periodic schedule.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261021_full_scan_schedule"
down_revision = "20261021_session_version"


def upgrade():
    op.add_column("sync_checkpoints", sa.Column("last_full_scan_at", sa.DateTime(), nullable=True))
    op.execute("""
        UPDATE sync_checkpoints SET last_full_scan_at = last_run_at
        WHERE status = 'idle' AND records_error = 0
          AND dataset IN ('agendas', 'votings', 'events', 'texts', 'groups', 'interests')
    """)
    # Affairs and meetings: only if their last run processed every local record,
    # i.e. it was a complete identity reconciliation.
    for dataset in ("affairs", "meetings"):
        op.execute(f"""
            UPDATE sync_checkpoints SET last_full_scan_at = last_run_at
            WHERE dataset = '{dataset}' AND status = 'idle' AND records_error = 0
              AND records_processed >= (SELECT count(*) FROM {dataset})
        """)
    # Datasets that newly use an updated_at cursor start from the newest
    # timestamp stored by their last complete comparison, instead of reading
    # every timestamped source record once more.
    for dataset in ("votings", "events", "texts", "groups", "interests"):
        op.execute(INITIAL_CURSOR.format(dataset=dataset))


INITIAL_CURSOR = """
    UPDATE sync_checkpoints SET
        last_updated_at = newest.updated_at,
        last_id = newest.id
    FROM (SELECT updated_at, id FROM {dataset} WHERE updated_at IS NOT NULL
          ORDER BY updated_at DESC, id DESC LIMIT 1) AS newest
    WHERE sync_checkpoints.dataset = '{dataset}'
      AND sync_checkpoints.last_updated_at IS NULL
      AND sync_checkpoints.last_full_scan_at IS NOT NULL
"""


def downgrade():
    op.drop_column("sync_checkpoints", "last_full_scan_at")
