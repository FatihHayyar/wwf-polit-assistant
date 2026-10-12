import unittest

from scripts.sync.events_sync import map_event


class EventMappingTests(unittest.TestCase):
    def test_live_scalar_does_not_erase_existing_translations(self):
        values = map_event({"id": 980691, "title": {"de": "Eingereicht"},
                            "title_harmonized": "Eingereicht", "actor": {}})
        self.assertNotIn("title_harmonized", values)
        self.assertEqual(values["title_de"], "Eingereicht")
        self.assertNotIn("title_harmonized_fr", values)
        self.assertNotIn("title_harmonized_de", values)

    def test_flat_export_translations_are_retained(self):
        values = map_event({"id": 1, "title_harmonized": "Eingereicht",
                            "title_harmonized_fr": "Depose", "title_harmonized_en": "Submitted"})
        self.assertEqual(values["title_harmonized_fr"], "Depose")
        self.assertEqual(values["title_harmonized_en"], "Submitted")

    def test_dictionary_and_null_translations_remain_supported(self):
        values = map_event({"id": 1, "title_harmonized": {"de": "Test", "en": "Test"}, "actor": None})
        self.assertEqual(values["title_harmonized_en"], "Test")
        self.assertIsNone(values["actor_de"])
        with self.assertRaises(ValueError):
            map_event({"id": 1, "title_harmonized": ["invalid"]})
