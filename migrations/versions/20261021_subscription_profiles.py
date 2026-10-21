"""Several named subscription profiles per user, including affair types.

Existing per-user filters (topics, cantons, keywords, datasets) become one
profile called "Mein Abonnement". The four previous tables are removed;
record watches stay unchanged.
"""
import json

from alembic import op
import sqlalchemy as sa

revision = "20261021_subscription_profiles"
down_revision = "20261021_full_scan_schedule"

OLD_TABLES = {
    "user_category_subscriptions": "category_id",
    "user_canton_subscriptions": "canton_key",
    "user_keyword_subscriptions": "keyword",
    "user_dataset_subscriptions": "dataset",
}
PROFILE_FIELDS = {
    "user_category_subscriptions": "category_ids",
    "user_canton_subscriptions": "canton_keys",
    "user_keyword_subscriptions": "keywords",
    "user_dataset_subscriptions": "datasets",
}


def upgrade():
    op.create_table(
        "subscription_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("category_ids", sa.JSON(), nullable=False),
        sa.Column("canton_keys", sa.JSON(), nullable=False),
        sa.Column("keywords", sa.JSON(), nullable=False),
        sa.Column("datasets", sa.JSON(), nullable=False),
        sa.Column("affair_types", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_subscription_profiles_user_id", "subscription_profiles", ["user_id"])

    bind = op.get_bind()
    profiles = {}
    for table, column in OLD_TABLES.items():
        for user_id, value in bind.execute(sa.text(f"SELECT user_id, {column} FROM {table} ORDER BY {column}")):
            profile = profiles.setdefault(user_id, {field: [] for field in PROFILE_FIELDS.values()})
            profile[PROFILE_FIELDS[table]].append(value)
    profile_table = sa.table(
        "subscription_profiles",
        sa.column("user_id", sa.BigInteger()), sa.column("name", sa.String()), sa.column("active", sa.Boolean()),
        *(sa.column(field, sa.JSON()) for field in (*PROFILE_FIELDS.values(), "affair_types")),
    )
    rows = [dict(user_id=user_id, name="Mein Abonnement", active=True, affair_types=[], **fields)
            for user_id, fields in profiles.items()]
    if rows:
        op.bulk_insert(profile_table, rows)

    for table in OLD_TABLES:
        op.drop_table(table)


def downgrade():
    op.create_table(
        "user_category_subscriptions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.BigInteger(),
                  sa.ForeignKey("classification_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "category_id", name="uq_user_category_subscriptions"),
    )
    op.create_table(
        "user_canton_subscriptions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canton_key", sa.String(2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "canton_key", name="uq_user_canton_subscriptions"),
    )
    op.create_table(
        "user_keyword_subscriptions",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("keyword", sa.String(200), primary_key=True),
    )
    op.create_table(
        "user_dataset_subscriptions",
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dataset", sa.String(50), primary_key=True),
    )
    bind = op.get_bind()
    # Only the first profile of each user can be represented in the old model.
    seen = set()
    for row in bind.execute(sa.text("SELECT user_id, category_ids, canton_keys, keywords, datasets "
                                    "FROM subscription_profiles ORDER BY id")):
        if row.user_id in seen:
            continue
        seen.add(row.user_id)
        values = [json.loads(value) if isinstance(value, str) else value for value in row[1:]]
        for (table, column), items in zip(OLD_TABLES.items(), values):
            for item in items or []:
                bind.execute(sa.text(f"INSERT INTO {table} (user_id, {column}) VALUES (:user_id, :value)"),
                             {"user_id": row.user_id, "value": item})
    op.drop_index("idx_subscription_profiles_user_id", "subscription_profiles")
    op.drop_table("subscription_profiles")
