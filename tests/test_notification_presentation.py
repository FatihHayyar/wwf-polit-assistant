import unittest
from types import SimpleNamespace
from unittest.mock import patch
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

import app.models
from app.db.database import Base
from app.models.entities import Document
from app.models.change_event import ChangeEvent
from app.services.entity_service import affair_changes
from app.services.notification_content import render_digest, change_identity


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class NotificationPresentationTests(unittest.TestCase):
    def event(self, **kwargs):
        return SimpleNamespace(dataset="documents", source_id=909063, change_type="created",
                               changes=None, description=None, **kwargs)

    def test_plain_text_and_html_have_distinct_links_and_unicode(self):
        event = self.event()
        title = 'Kantonaler Richtplan: Bericht gemäß <script>alert(1)</script>'
        with patch("app.services.notification_content.settings") as settings:
            settings.verification_base_url = "http://localhost:8000"
            subject, body, html = render_digest(title, "affairs", 335547, [(event, None, "Erläuterungsbericht Windenergie")])
        self.assertIn("Neues Dokument", subject)
        self.assertNotIn(" ? ", subject)
        self.assertIn("Dokument öffnen: http://localhost:8000/?dataset=documents&record=909063", body)
        self.assertIn("Geschäft und Verlauf ansehen", body)
        self.assertNotIn("[Details", body)
        self.assertNotIn("\\", body)
        self.assertIn("&amp;record=909063", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("Abonnements verwalten", html)

    def test_document_variants_deduplicate_without_merging_different_sources(self):
        event = self.event()
        first = change_identity(event, SimpleNamespace(source_id=10))
        self.assertEqual(first, change_identity(event, SimpleNamespace(source_id=10)))
        self.assertNotEqual(first, change_identity(event, SimpleNamespace(source_id=11)))

    def test_history_has_titles_local_ids_and_preserves_different_updates(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            db.add_all([Document(pk=1,source_id=10,name="Windbericht"),
                        Document(pk=2,source_id=10,name="Windbericht"),
                        Document(pk=3,source_id=11,name="Windbericht")])
            for index, pk in enumerate([1,2,3,999],1):
                db.add(ChangeEvent(dataset="documents",source_id=pk,affair_id=1,
                                   change_type="created",fingerprint=str(index)*64))
            for index, changes in enumerate([{"text":{"before":"a","after":"b"}},
                                             {"text":{"before":"b","after":"c"}}],5):
                db.add(ChangeEvent(dataset="documents",source_id=1,affair_id=1,
                                   change_type="updated",fingerprint=str(index)*64,changes=changes))
            db.commit()
            history = affair_changes(db,1)
        engine.dispose()
        self.assertEqual(len(history),5)
        self.assertEqual(sum(row["change_type"]=="updated" for row in history),2)
        self.assertEqual(sum(row["title"]=="Windbericht" for row in history),4)
        deleted = next(row for row in history if row["source_id"]==999)
        self.assertFalse(deleted["available"])
        self.assertTrue(all(row["available"] for row in history if row["source_id"]!=999))
