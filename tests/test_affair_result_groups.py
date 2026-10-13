import unittest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.db.database import Base
from app.models.entities import Affair
from app.services.entity_service import list_entities, search_all_entities


class AffairResultGroupTests(unittest.TestCase):
    def test_same_project_sources_share_one_card_and_pagination_keeps_other_projects(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            title = "Projet de loi protection du climat"
            db.add_all([
                Affair(id=1, body_id=260, title_fr=title, number="2026-M-9", type_name_fr="Message", begin_date=datetime(2026, 10, 2, 9)),
                Affair(id=2, body_id=260, title_fr=title, number="LOI 2026.10.02-1", type_name_fr="Projet de loi", begin_date=datetime(2026, 10, 2)),
                Affair(id=3, body_id=260, title_fr=title, begin_date=datetime(2026, 10, 3)),
                Affair(id=4, body_id=261, title_fr=title, begin_date=datetime(2026, 10, 2)),
                Affair(id=5, body_id=260, title_fr=None, begin_date=datetime(2026, 10, 2)),
                Affair(id=6, body_id=260, title_fr=None, begin_date=datetime(2026, 10, 2)),
            ])
            db.commit()
            result = list_entities(db, "affairs", q="protection du climat")
            self.assertEqual(result["pagination"]["total_items"], 3)
            grouped = next(item for item in result["items"] if item["id"] == 2)
            self.assertEqual([item["id"] for item in grouped["record_variants"]], [1, 2])
            self.assertEqual(len(list_entities(db, "affairs")["items"]), 5)
            ids = [list_entities(db, "affairs", q="protection du climat", page=page, page_size=1)["items"][0]["id"] for page in (1, 2, 3)]
            self.assertEqual(set(ids), {2, 3, 4})
            combined = search_all_entities(db, ["affairs"], q="protection du climat")
            self.assertEqual(combined["pagination"]["total_items"], 3)
            self.assertEqual({item["id"] for item in combined["items"]}, {2, 3, 4})
            by_number = search_all_entities(db, ["affairs"], q="2026-M-9")
            self.assertEqual([item["id"] for item in by_number["items"]], [1])
            self.assertEqual(db.query(Affair).count(), 6)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
