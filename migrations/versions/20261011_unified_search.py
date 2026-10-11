"""Index unified searches across all nine datasets."""
from alembic import op
import sqlalchemy as sa
revision = "20261011_unified_search"
down_revision = "20261011_notification_policy"
branch_labels = None
depends_on = None

STATEMENTS = ['CREATE INDEX IF NOT EXISTS idx_affairs_content_search ON "affairs" USING gin ((lower(coalesce(title_de, \'\') || \'\n\' || coalesce(title_fr, \'\') || \'\n\' || coalesce(title_it, \'\') || \'\n\' || coalesce(number, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_agendas_content_search ON "agendas" USING gin ((lower(coalesce(item_title, \'\') || \'\n\' || coalesce(item_description, \'\') || \'\n\' || coalesce(item_affair_number, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_meetings_content_search ON "meetings" USING gin ((lower(coalesce(name_de, \'\') || \'\n\' || coalesce(name_fr, \'\') || \'\n\' || coalesce(name_it, \'\') || \'\n\' || coalesce(description_de, \'\') || \'\n\' || coalesce(location, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_votings_content_search ON "votings" USING gin ((lower(coalesce(title_de, \'\') || \'\n\' || coalesce(title_fr, \'\') || \'\n\' || coalesce(title_it, \'\') || \'\n\' || coalesce(decision, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_events_content_search ON "events" USING gin ((lower(coalesce(title_de, \'\') || \'\n\' || coalesce(title_fr, \'\') || \'\n\' || coalesce(title_it, \'\') || \'\n\' || coalesce(details_text, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_documents_content_search ON "documents" USING gin ((lower(coalesce(name, \'\') || \'\n\' || coalesce(text, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_texts_content_search ON "texts" USING gin ((lower(coalesce(text_de, \'\') || \'\n\' || coalesce(text_fr, \'\') || \'\n\' || coalesce(text_it, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_groups_content_search ON "groups" USING gin ((lower(coalesce(name_de, \'\') || \'\n\' || coalesce(name_fr, \'\') || \'\n\' || coalesce(name_it, \'\') || \'\n\' || coalesce(abbreviation_de, \'\') || \'\n\' || coalesce(abbreviation_fr, \'\') || \'\n\' || coalesce(abbreviation_it, \'\'))) gin_trgm_ops)', 'CREATE INDEX IF NOT EXISTS idx_interests_content_search ON "interests" USING gin ((lower(coalesce(name_de, \'\') || \'\n\' || coalesce(name_fr, \'\') || \'\n\' || coalesce(name_it, \'\') || \'\n\' || coalesce(declaration_doc_title, \'\') || \'\n\' || coalesce(role_name_de, \'\') || \'\n\' || coalesce(role_name_fr, \'\') || \'\n\' || coalesce(role_name_it, \'\'))) gin_trgm_ops)']

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    with op.get_context().autocommit_block():
        for statement in STATEMENTS:
            index_name = statement.split()[5]
            valid = op.get_bind().scalar(sa.text("SELECT indisvalid FROM pg_index WHERE indexrelid=to_regclass(:name)"), {"name": index_name})
            if valid is False:
                op.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{index_name}"')
            if 'idx_documents_content_search' in statement or 'idx_texts_content_search' in statement:
                statement = statement.replace('USING gin ((lower(', "USING gin ((to_tsvector('simple'::regconfig, left(lower(")
                statement = statement.replace(')) gin_trgm_ops)', '), 100000))) )')
            op.execute(statement.replace("CREATE INDEX IF NOT EXISTS", "CREATE INDEX CONCURRENTLY IF NOT EXISTS"))

def downgrade():
    for dataset in ['affairs', 'agendas', 'meetings', 'votings', 'events', 'documents', 'texts', 'groups', 'interests']:
        op.execute(f'DROP INDEX IF EXISTS idx_{dataset}_content_search')
