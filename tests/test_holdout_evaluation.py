"""Integrity of the held-out classification sample and its scoring rules.

These tests deliberately contain no quality threshold: tuning rules until a
held-out score passes would turn the sample into a second development set.
"""
import json
import unittest
from pathlib import Path

from app.classification.taxonomy import load_taxonomy
from scripts.evaluate_holdout import (
    OTHER,
    binary_metrics,
    load_fixture,
    main_topic_metrics,
    parent_map,
    score_record,
    wilson_interval,
)


class HoldoutFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()
        cls.parents = parent_map(load_taxonomy())

    def test_sample_is_disjoint_from_development_set(self):
        development = json.loads(Path("tests/fixtures/rule_quality_50.json").read_text(encoding="utf-8"))["records"]
        development_ids = {r["id"] for r in development if r["dataset"] == "affairs"}
        holdout_ids = [r["id"] for r in self.fixture["records"]]
        self.assertEqual(len(holdout_ids), 300)
        self.assertEqual(len(set(holdout_ids)), 300)
        self.assertFalse(development_ids & set(holdout_ids))

    def test_every_label_is_a_taxonomy_code(self):
        for record in self.fixture["records"]:
            expected = record["expected"]
            codes = set(expected["required"]) | set(expected["optional"])
            codes |= {code for group in expected.get("required_any", []) for code in group}
            with self.subTest(id=record["id"]):
                self.assertTrue(codes)
                self.assertLessEqual(codes, set(self.parents))

    def test_ambiguous_records_accept_other(self):
        for record in self.fixture["records"]:
            expected = record["expected"]
            if not expected["required"] and not expected.get("required_any"):
                with self.subTest(id=record["id"]):
                    self.assertIn(OTHER, expected["optional"])


class HoldoutScoringTests(unittest.TestCase):
    parents = {"climate": "climate", "solar": "climate", "forest": "nature", "nature": "nature", OTHER: OTHER}

    def test_strict_score_accepts_optional_and_any_group(self):
        expected = {"required": ["solar"], "optional": ["climate"], "required_any": [["forest", "nature"]]}
        self.assertTrue(score_record(expected, {"solar", "forest"})["correct"])
        self.assertTrue(score_record(expected, {"solar", "climate", "nature"})["correct"])
        self.assertEqual(score_record(expected, {"solar"})["missing_any"], [["forest", "nature"]])
        self.assertEqual(score_record(expected, {"solar", "forest", OTHER})["extra"], [OTHER])

    def test_binary_metrics_ignore_ambiguous_records(self):
        records = [
            {"id": 1, "expected": {"required": ["solar"], "optional": []}},
            {"id": 2, "expected": {"required": [OTHER], "optional": []}},
            {"id": 3, "expected": {"required": [], "optional": ["forest", OTHER]}},
            {"id": 4, "expected": {"required": [], "optional": [], "required_any": [["forest"]]}},
        ]
        predictions = {1: {"solar"}, 2: {"forest"}, 3: {"forest"}, 4: {OTHER}}
        metrics = binary_metrics(records, predictions)
        self.assertEqual((metrics["tp"], metrics["fp"], metrics["fn"], metrics["tn"]), (1, 1, 1, 0))
        self.assertEqual(metrics["records"], 3)
        self.assertEqual(metrics["precision"], 0.5)

    def test_main_topic_metrics_use_parent_topics(self):
        records = [{"id": 1, "expected": {"required": ["solar"], "optional": []}},
                   {"id": 2, "expected": {"required": [OTHER], "optional": []}}]
        metrics = main_topic_metrics(records, {1: {"climate"}, 2: {"forest"}}, self.parents)
        self.assertEqual(metrics["counts"], {"tp": 1, "fp": 1})
        self.assertEqual(metrics["topics"]["nature"]["fp"], 1)

    def test_wilson_interval_is_bounded(self):
        self.assertEqual(wilson_interval(0, 0), None)
        low, high = wilson_interval(13, 40)
        self.assertLess(low, 13 / 40)
        self.assertGreater(high, 13 / 40)
        self.assertEqual(wilson_interval(10, 10)[1], 1.0)


if __name__ == "__main__":
    unittest.main()
