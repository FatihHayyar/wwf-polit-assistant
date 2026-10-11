"""Baseline application schema.

The initial OpenParlData snapshot was imported and validated before
Alembic became the authoritative schema migration mechanism.

This revision preserves existing imported tables and creates the original
parliamentary tables when starting with an empty database.

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
    """Retain imported tables; create the original schema on an empty database."""
    from alembic import op
    import sqlalchemy as sa
    from app.db.database import Base
    import app.models

    original = sa.MetaData()
    for name in ('bodies', 'persons', 'groups', 'memberships', 'interests',
                 'affairs', 'meetings', 'agendas', 'events', 'votings',
                 'documents', 'texts'):
        source = Base.metadata.tables[name]
        table = sa.Table(name, original, *(
            sa.Column(c.name, c.type, primary_key=c.primary_key,
                      nullable=c.nullable, autoincrement=c.autoincrement)
            for c in source.columns if c.name != 'sync_fingerprint'
        ))
        for index in source.indexes:
            if index.name != 'idx_meetings_group_id':
                sa.Index(index.name, *(table.c[c.name] for c in index.columns),
                         unique=index.unique)
    original.create_all(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """The baseline does not remove the pre-existing application schema."""
    pass
