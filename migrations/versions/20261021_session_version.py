"""Session version on users so that logout revokes issued access tokens."""
from alembic import op
import sqlalchemy as sa

revision = "20261021_session_version"
down_revision = "20261012_recipients"


def upgrade():
    op.add_column(
        "users",
        sa.Column("session_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("users", "session_version")
