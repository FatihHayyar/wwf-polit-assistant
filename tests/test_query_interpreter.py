"""Dialogue-oriented query: question interpretation and the /api/v1/ask endpoint."""
import unittest
from datetime import date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.routes.ask as ask_route
import app.models  # noqa: F401  (registers all tables on Base.metadata)
from app.core.rate_limit import limiter
from app.db.database import Base, get_db
from app.main import app as fastapi_app
from app.models.classification import AffairClassification, ClassificationCategory
from app.models.entities import Affair, Body
from app.services.entity_service import list_entities
from app.services.query_interpreter import RuleBasedInterpreter
from scripts.seed_classification import seed_taxonomy


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


TODAY = date(2026, 10, 21)
TYPES = ["Anfrage", "Interpellation", "Motion", "Postulat"]


class InterpreterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite://")
        Base.metadata.create_all(cls.engine)
        cls.db = Session(cls.engine)
        seed_taxonomy(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        cls.engine.dispose()

    def interpret(self, question):
        result = RuleBasedInterpreter().interpret(self.db, question, TYPES, TODAY)
        return result.dataset, result.filters()

    def test_topic_canton_and_affair_type(self):
        self.assertEqual(self.interpret("Motionen zum Wolf im Wallis"), ("affairs", {
            "category": "biodiversity_landscape", "subcategory": "species_habitats", "canton": "VS", "affair_type": "Motion"}))

    def test_since_year_and_french_question(self):
        dataset, filters = self.interpret("Interpellationen zu Photovoltaik in Bern seit 2024")
        self.assertEqual((filters["subcategory"], filters["canton"], filters["affair_type"], filters["date_from"]),
                         ("renewable_electricity", "BE", "Interpellation", date(2024, 1, 1)))
        self.assertEqual(self.interpret("Votations sur le climat à Genève")[0], "votings")

    def test_dataset_and_relative_period_without_keyword_noise(self):
        self.assertEqual(self.interpret("Sitzungen im Kanton Zürich letzten Monat"), ("meetings", {
            "canton": "ZH", "date_from": date(2026, 9, 1), "date_to": date(2026, 9, 30)}))
        self.assertEqual(self.interpret("sedute in Ticino"), ("meetings", {"canton": "TI"}))

    def test_quoted_phrase_becomes_keyword_and_capital_code_is_canton(self):
        _, filters = self.interpret('Was gibt es zu "Fernwärme" im Kanton BE?')
        self.assertEqual((filters["q"], filters["canton"]), ("Fernwärme", "BE"))
        # Lower-case "so" is a word, not the canton Solothurn.
        self.assertNotIn("canton", self.interpret("Was gibt es so zum Wald?")[1])

    def test_main_topic_word_and_last_year(self):
        self.assertEqual(self.interpret("Welche Abstimmungen zum Klima gab es letztes Jahr?"), ("votings", {
            "category": "climate_energy", "date_from": date(2025, 1, 1), "date_to": date(2025, 12, 31)}))

    def test_unknown_question_falls_back_to_keyword(self):
        self.assertEqual(self.interpret("Seilbahnprojekte"), ("affairs", {"q": "seilbahnprojekte"}))


class AskEndpointTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        Session_ = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        with Session_() as db:
            seed_taxonomy(db)
            db.add_all([Body(id=1, canton_key="VS"), Body(id=2, canton_key="BE")])
            for affair_id, body_id, affair_type in [(1, 1, "Motion"), (2, 1, "Postulat"), (3, 2, "Motion")]:
                db.add(Affair(id=affair_id, body_id=body_id, title_de=f"Wolf {affair_id}", type_harmonized_de=affair_type,
                              begin_date=datetime(2026, 1, affair_id)))
            db.flush()
            species = db.scalar(select(ClassificationCategory.id).where(ClassificationCategory.code == "species_habitats"))
            for affair_id in (1, 2, 3):
                db.add(AffairClassification(affair_id=affair_id, category_id=species, score=10, confidence="high",
                                            classifier_version="test", classified_at=datetime(2026, 1, 1)))
            db.commit()
        self.Session = Session_

        def override_db():
            with Session_() as db:
                yield db

        fastapi_app.dependency_overrides[get_db] = override_db
        ask_route._affair_types_cache = (0.0, [])
        limiter.reset()
        self.client = TestClient(fastapi_app)

    def tearDown(self):
        fastapi_app.dependency_overrides.clear()
        ask_route._affair_types_cache = (0.0, [])
        self.engine.dispose()

    def test_question_returns_filters_and_matching_records(self):
        answer = self.client.post("/api/v1/ask", json={"question": "Motionen zum Wolf im Wallis"}).json()
        self.assertEqual(answer["dataset"], "affairs")
        self.assertEqual(answer["filters"]["affair_type"], "Motion")
        self.assertEqual({item["kind"] for item in answer["recognised"]}, {"dataset", "subcategory", "canton", "affair_type"})
        self.assertEqual([item["id"] for item in answer["results"]["items"]], [1])

    def test_invalid_question_and_rate_limit(self):
        self.assertEqual(self.client.post("/api/v1/ask", json={"question": "x"}).status_code, 422)
        codes = [self.client.post("/api/v1/ask", json={"question": "Wolf"}).status_code for _ in range(31)]
        self.assertEqual(codes[-1], 429)

    def test_affair_type_filter_applies_only_to_affairs(self):
        with self.Session() as db:
            self.assertEqual(list_entities(db, "affairs", affair_type="Motion")["pagination"]["total_items"], 2)
            self.assertEqual(list_entities(db, "affairs", affair_type="Postulat", canton="VS")["pagination"]["total_items"], 1)
            self.assertEqual(list_entities(db, "agendas", affair_type="Motion")["pagination"]["total_items"], 0)
        types = self.client.get("/api/v1/affair-types").json()
        self.assertEqual({item["value"] for item in types}, {"Motion", "Postulat"})


if __name__ == "__main__":
    unittest.main()
