import copy
import json
import unittest
from pathlib import Path
from types import MethodType, SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.classification.classifier import AffairClassifier, build_phrase_pattern, normalize_text
from app.classification.taxonomy import load_taxonomy
from app.db.database import Base
from app.services.category_service import get_categories
from scripts.rule_quality import evaluate, score
from scripts.seed_classification import seed_taxonomy


class RuleClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(cls.engine)
        cls.db = Session(cls.engine)
        seed_taxonomy(cls.db)
        cls.classifier = AffairClassifier(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.engine.dispose()

    def codes(self, title):
        return {self.classifier.categories[m.category_id].code for m in
                self.classifier.accepted_matches(SimpleNamespace(id=1, title_de=title,
                    **{field: None for field in ("title_long_de", "title_fr", "title_long_fr", "title_it",
                       "title_long_it", "title_rm", "title_long_rm")}), [])}

    def test_real_mixed_examples(self):
        records = json.loads(Path("tests/fixtures/rule_quality_50.json").read_text(encoding="utf-8"))["records"]
        results = evaluate(load_taxonomy(), AffairClassifier, records)
        for result in results:
            with self.subTest(dataset=result["dataset"], id=result["id"]):
                self.assertTrue(result["correct"], result)

    def test_negative_words_and_generic_administration_are_not_environment_topics(self):
        for title in ["Waldemar im Gemeinderat", "COPPER und Polizeireform", "Schulraumplanung",
                "Forschung und Lehre", "Lebensraum für Studierende", "Gemeindeverwaltung Förderprogramm Vorbildfunktion",
                "Förderprogramm für Theater", "Mitarbeiter und Ressourcenverbrauch in der Verwaltung",
                "Digitale Netze und Datenspeicher", "Arbeitsbedingungen an der Universität",
                "Ökologische Kriterien für Unternehmen", "Budget 2026", "Kantonale Verwaltung Vorbildfunktion"]:
            with self.subTest(title=title):
                self.assertEqual(self.codes(title), set())

    def test_specific_leaf_excludes_only_its_own_parent_fallback(self):
        self.assertEqual(self.codes("Klimaschutz und Photovoltaikanlagen"), {"renewable_electricity"})
        self.assertEqual(self.codes("Klimakrise und Kreislaufwirtschaft"),
                         {"climate_energy_other", "circular_economy"})

    def test_qualified_public_role_needs_environment_and_actor(self):
        self.assertEqual(self.codes("Öffentliche Beschaffung"), set())
        self.assertEqual(self.codes("Ökologische Beschaffung der öffentlichen Hand"), {"public_sector"})
        self.assertEqual(self.codes("Ökologische Kriterien"), set())

    def test_prefixes_preserve_word_boundaries_and_short_names(self):
        self.assertTrue(build_phrase_pattern("photovoltaik", "prefix").search("photovoltaikanlage"))
        self.assertFalse(build_phrase_pattern("photovoltaik", "prefix").search("antiphotovoltaik"))
        self.assertFalse(build_phrase_pattern("wald", "prefix").search("waldemar"))
        self.assertEqual(normalize_text("<p>CO<sub>2</sub> &amp; Wär-\nmenetze</p>"), "co2 & wärmenetze")

    def test_malformed_source_markup_keeps_the_substantive_text(self):
        source = "<![e\r\n\t[><p>Photovoltaikanlage und Windenergie</p>"
        self.assertIn("photovoltaikanlage und windenergie", normalize_text(source))
        self.assertEqual(self.codes(source), {"renewable_electricity"})

    def test_index_preserves_all_overlapping_rule_matches(self):
        indexed = self.classifier
        brute = copy.copy(indexed)
        def match_text(self, matches, *, value, language, scope, source_type, source_id):
            value = normalize_text(value)
            for rule in self.rules[scope][language]:
                if rule.pattern.search(value):
                    self._add_evidence(matches, rule=rule, source_type=source_type, source_id=source_id)
        brute._match_text = MethodType(match_text, brute)
        source = SimpleNamespace(id=1, title_de="Klimaschutzgesetz und Photovoltaikanlagen, erneuerbarer Strom",
            **{field: None for field in ("title_long_de", "title_fr", "title_long_fr", "title_it",
               "title_long_it", "title_rm", "title_long_rm")})
        def signature(matches):
            return sorted((m.category_id, m.score, sorted(m.matched_terms)) for m in matches)
        self.assertEqual(signature(indexed.classify_title(source)), signature(brute.classify_title(source)))

    def test_category_api_shows_local_other_under_all_four_parents(self):
        parents = get_categories(self.db)
        self.assertEqual(len(parents), 4)
        for parent in parents:
            self.assertEqual(sum(c.code == parent.code + "_other" for c in parent.subcategories), 1)

    def test_configuration_changes_names_adds_and_deactivates_categories_idempotently(self):
        taxonomy = copy.deepcopy(load_taxonomy())
        taxonomy[0]["names"]["de"] = "Testname"
        taxonomy[0]["children"].append({"code": "test_extra", "names": {lang: "Test" for lang in ("de", "fr", "it", "rm")}, "concepts": []})
        engine = create_engine("sqlite:///:memory:")
        try:
            Base.metadata.create_all(engine)
            with Session(engine) as db:
                seed_taxonomy(db, taxonomy)
                seed_taxonomy(db, taxonomy)
                self.assertEqual(get_categories(db)[0].name_de, "Testname")
                self.assertIn("test_extra", {c.code for c in get_categories(db)[0].subcategories})
                seed_taxonomy(db, load_taxonomy())
                self.assertNotIn("test_extra", {c.code for p in get_categories(db) for c in p.subcategories})
        finally:
            engine.dispose()
