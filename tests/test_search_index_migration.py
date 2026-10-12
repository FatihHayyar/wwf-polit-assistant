import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch


class SearchIndexMigrationTests(unittest.TestCase):
    def migrate(self, options):
        path = Path(__file__).resolve().parents[1] / "migrations/versions/20261011_unified_search.py"
        spec = importlib.util.spec_from_file_location("search_index_migration_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        operations = MagicMock()
        operations.get_bind.return_value.scalar.return_value = True
        with patch.object(module, "op", operations), patch.object(module.context, "get_x_argument", return_value=options):
            module.upgrade()
        return [call.args[0] for call in operations.execute.call_args_list if call.args[0].startswith("CREATE INDEX")]

    def test_operator_can_defer_only_large_experimental_indexes(self):
        statements = self.migrate({"skip_large_search_indexes": "true"})
        self.assertEqual(len(statements), 7)
        self.assertFalse(any("idx_documents_content_search" in statement or "idx_texts_content_search" in statement for statement in statements))
        self.assertTrue(all("CONCURRENTLY" in statement for statement in statements))

    def test_default_keeps_existing_migration_behavior(self):
        statements = self.migrate({})
        self.assertEqual(len(statements), 9)
        large = [statement for statement in statements if "to_tsvector" in statement]
        self.assertEqual(len(large), 2)
        self.assertTrue(all("100000" in statement for statement in large))
