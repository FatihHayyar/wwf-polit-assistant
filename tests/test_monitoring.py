"""Offline regression tests; no production database or SMTP access."""
import unittest
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import BigInteger, create_engine, func, select, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from app.db.database import Base
import app.models
from app.models import Affair, Agenda, Body, Meeting, Document, ParliamentaryText, User, Notification, PoliticalGroup, Interest, Person
from app.models.classification import AffairClassification, ClassificationCategory, ClassificationRule, ClassificationEvidence
from app.models.change_event import ChangeEvent
from app.models.change_event_affair import ChangeEventAffair
from app.models.dataset_subscription import UserDatasetSubscription
from app.models.subscription import UserCategorySubscription, UserCantonSubscription
from app.schemas.affair_filters import AffairFilters
from app.services.affair_service import get_affairs, get_affair_detail
from app.services.entity_service import list_entities
from scripts.sync.entity_sync import choose_document, sync_record
from app.services.entity_relations import related_affair_ids
from app.models.entity_classification import EntityClassification
from app.models.monitoring_subscription import UserKeywordSubscription, UserRecordWatch


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False)
        for cat_id, code, parent, fallback in [(1,"climate",None,False),(2,"solar",1,False),(3,"wind",1,False),(4,"other",None,True)]:
            self.db.add(ClassificationCategory(id=cat_id,code=code,parent_id=parent,
                name_de=code,name_fr=code,name_it=code,name_rm=code,active=True,is_fallback=fallback,sort_order=0,classification_threshold=8))
        self.db.add(Body(id=1,canton_key="BE"))
        self.db.add(Body(id=2,canton_key="ZH"))
        self.db.add(Affair(id=1,body_id=1,title_de="Photovoltaik",begin_date=datetime(2026,1,1),state_name_harmonized_de="open"))
        self.db.add(Affair(id=2,body_id=2,title_de="Windenergie",begin_date=datetime(2026,1,2),state_name_harmonized_de="closed"))
        self.db.add(Meeting(id=1,body_id=1,name_de="Sitzung",begin_date=datetime(2026,1,2),updated_at=datetime(2026,1,1)))
        self.db.add(Agenda(id=1,body_id=1,meeting_id=1,item_affair_id=1,item_title="Solar",item_date=datetime(2026,1,2)))
        self.db.add(Agenda(id=2,body_id=2,meeting_id=1,item_affair_id=2,item_title="Wind",item_date=datetime(2026,1,3)))
        self.db.flush()
        for affair_id,cat_id in [(1,2),(1,3),(2,3)]:
            self.db.add(AffairClassification(affair_id=affair_id,category_id=cat_id,score=10,confidence="high",classifier_version="test",classified_at=datetime(2026,1,1)))
        self.db.add(User(id=1,email="test@example.com",is_active=True,email_verified=True,is_admin=False))
        self.db.flush()
        self.db.add(UserCategorySubscription(user_id=1,category_id=1))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def count(self, model):
        return self.db.scalar(select(func.count()).select_from(model))

    def test_keyword_subscription_requires_keyword_and_canton(self):
        self.db.add(UserKeywordSubscription(user_id=1, keyword="solaranlage"))
        self.db.add(UserCantonSubscription(user_id=1, canton_key="BE"))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":1,"item_title":"Neue Sitzung"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),0)
        sync_record(self.db,"agendas",{"id":1,"item_title":"Neue SOLARANLAGE"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),1)
        sync_record(self.db,"agendas",{"id":2,"item_title":"Neue Solaranlage"},self.db.get(Agenda,2))
        self.db.commit()
        self.assertEqual(self.count(Notification),1)

    def test_keyword_only_subscription(self):
        self.db.query(UserCategorySubscription).delete()
        self.db.add(UserKeywordSubscription(user_id=1, keyword="wärmepumpe"))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":50,"body_id":1,"item_title":"Wärmepumpe für Schule"})
        self.db.commit()
        self.assertEqual(self.count(Notification),1)

    def test_affair_watch_survives_category_and_dataset_changes(self):
        self.db.query(UserCategorySubscription).delete()
        self.db.add(UserRecordWatch(user_id=1, dataset="affairs", record_id=1))
        self.db.add(UserDatasetSubscription(user_id=1, dataset="texts"))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":1,"item_title":"Verfahren geändert"},self.db.get(Agenda,1))
        sync_record(self.db,"agendas",{"id":2,"item_title":"Anderes Verfahren"},self.db.get(Agenda,2))
        self.db.commit()
        self.assertEqual(self.count(Notification),1)

    def test_meeting_watch_includes_linked_agenda(self):
        self.db.query(UserCategorySubscription).delete()
        self.db.add(UserRecordWatch(user_id=1, dataset="meetings", record_id=1))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":1,"item_title":"Agenda geändert"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),1)

    def test_unwatch_cancels_pending_email(self):
        from app.services.notification_email_service import send_pending_notifications
        self.db.query(UserCategorySubscription).delete()
        self.db.add(UserRecordWatch(user_id=1, dataset="affairs", record_id=1))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":1,"item_title":"Neue Agenda"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),1)
        self.db.query(UserRecordWatch).delete()
        self.db.commit()
        with patch("app.services.notification_email_service.SessionLocal",side_effect=lambda:Session(self.engine)), patch("app.services.notification_email_service.send_email") as send:
            self.assertEqual(send_pending_notifications(),(0,0))
            send.assert_not_called()

    def test_subscription_keyword_roundtrip_and_clear_watches(self):
        from app.api.routes.subscriptions import SubscriptionUpdate, update_all_subscriptions, subscription_summary, watch_record
        from fastapi import HTTPException
        user = self.db.get(User,1)
        watch_record("affairs",1,user,self.db)
        watch_record("affairs",1,user,self.db)
        self.assertEqual(self.count(UserRecordWatch),1)
        with self.assertRaises(HTTPException):
            watch_record("affairs",999,user,self.db)
        with patch("app.api.routes.subscriptions.send_email"):
            update_all_subscriptions(SubscriptionUpdate(keywords=["  Solar  ","solar"]),user,self.db)
            result=subscription_summary(user,self.db)
            self.assertEqual(result["keywords"],["solar"])
            self.assertTrue(result["active"])
            update_all_subscriptions(SubscriptionUpdate(clear_watches=True),user,self.db)
        self.assertFalse(subscription_summary(user,self.db)["active"])

    def test_category_filter_and_pagination(self):
        result=list_entities(self.db,"affairs",category="climate",page_size=1)
        self.assertEqual(result["pagination"]["total_items"],2)
        self.assertEqual(len(result["items"]),1)
        old=get_affairs(self.db,AffairFilters(category="climate"))
        self.assertEqual(len(old.items),2)

    def test_state_filter(self):
        self.assertEqual([item.id for item in get_affairs(self.db,AffairFilters(state="closed")).items],[2])

    def test_related_category_filters_all_datasets(self):
        self.db.add(Document(source_id=30,body_id=1,agenda_id=1,name="Solar document"))
        self.db.add(ParliamentaryText(id=30,body_id=2,affair_id=2,text_de="Wind text"))
        self.db.commit()
        for dataset in ("agendas","meetings","documents","texts"):
            result=list_entities(self.db,dataset,category="climate")
            self.assertGreater(result["pagination"]["total_items"],0,dataset)
        result=list_entities(self.db,"agendas",affair_id=1)
        self.assertEqual([row["id"] for row in result["items"]],[1])

    def test_keyword_canton_dates(self):
        result=list_entities(self.db,"agendas",q="Solar",canton="BE",year=2026,month=1)
        self.assertEqual([row["id"] for row in result["items"]],[1])
        self.assertEqual(list_entities(self.db,"agendas",q="Solar",canton="ZH")["items"],[])

    def test_timestamp_only_no_event(self):
        meeting=self.db.get(Meeting,1)
        result=sync_record(self.db,"meetings",{"id":1,"updated_at":datetime(2026,2,1)},meeting)
        self.db.commit()
        self.assertEqual(result,"UNCHANGED")
        self.assertEqual(self.count(ChangeEvent),0)
        self.assertEqual(self.count(Notification),0)

    def test_agenda_change_updates_affair_history(self):
        result=sync_record(self.db,"agendas",{"id":1,"item_title":"Neue Solaranlage"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(result,"CHANGED")
        self.assertEqual(self.count(Notification),1)
        detail=get_affair_detail(self.db,1)
        self.assertEqual(detail.changes[0]["dataset"],"agendas")
        self.assertEqual(detail.related["agendas"]["items"][0]["title"],"Neue Solaranlage")
        sync_record(self.db,"agendas",{"id":1,"item_title":"Neue Solaranlage"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(ChangeEvent),1)

    def test_meeting_fanout_single_notification(self):
        sync_record(self.db,"meetings",{"id":1,"location":"Neuer Ort"},self.db.get(Meeting,1))
        self.db.commit()
        self.assertEqual(self.count(ChangeEventAffair),2)
        self.assertEqual(self.count(Notification),1)
        for affair_id in (1,2):
            self.assertEqual(get_affair_detail(self.db,affair_id).changes[0]["dataset"],"meetings")

    def test_return_to_previous_content_is_a_new_change(self):
        for title in ("Version A","Version B","Version A","Version A"):
            sync_record(self.db,"agendas",{"id":1,"item_title":title},self.db.get(Agenda,1))
            self.db.commit()
        self.assertEqual(self.count(ChangeEvent),3)
        self.assertEqual(self.count(Notification),3)

    def test_dataset_subscription(self):
        self.db.add(UserDatasetSubscription(user_id=1,dataset="texts"))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":1,"item_title":"Changed"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),0)

    def test_document_identity(self):
        rows=[Document(source_id=10,affair_id=1),Document(source_id=10,affair_id=2)]
        self.assertIs(choose_document(rows,{"source_id":10,"affair_id":2}),rows[1])
        self.assertIsNone(choose_document(rows,{"source_id":10,"affair_id":3}))
        with self.assertRaises(ValueError):
            choose_document([rows[0],rows[0]],{"source_id":10,"affair_id":1})

    def test_direct_affair_does_not_match_other_meeting_affairs(self):
        self.assertEqual(related_affair_ids(self.db,"documents",Document(source_id=70,affair_id=1,meeting_id=1)),{1})

    def add_rule(self, term, concept, scope="title"):
        self.db.add(ClassificationRule(category_id=2,concept_code=concept,language="de",term=term,
            scope=scope,rule_type="strong",weight=10 if scope=="title" else 4,active=True,match_type="phrase"))
        self.db.commit()

    def test_standalone_entity_classified_and_notified(self):
        self.add_rule("Photovoltaik","solar_title")
        sync_record(self.db,"agendas",{"id":50,"body_id":1,"item_title":"Photovoltaik"})
        self.db.commit()
        self.assertEqual(self.count(Notification),1)
        result=list_entities(self.db,"agendas",category="climate",q="Photovoltaik")
        self.assertEqual({item["id"] for item in result["items"]},{1,50})

    def test_text_replaces_stale_classification(self):
        self.db.get(Affair,1).title_de="Allgemeiner Bericht"
        self.db.commit()
        self.add_rule("Photovoltaik","photovoltaics","content")
        self.add_rule("Solaranlage","solar_installation","content")
        sync_record(self.db,"texts",{"id":60,"body_id":1,"affair_id":1,"text_de":"Photovoltaik und Solaranlage"})
        self.db.commit()
        category_ids=set(self.db.scalars(select(AffairClassification.category_id).where(AffairClassification.affair_id==1)))
        self.assertEqual(category_ids,{2})
        self.assertEqual(self.count(Notification),1)

    def test_email_rechecks_current_subscription(self):
        from app.services.notification_email_service import send_pending_notifications
        sync_record(self.db,"agendas",{"id":1,"item_title":"Neue Traktanden"},self.db.get(Agenda,1))
        self.db.commit()
        self.db.query(UserCategorySubscription).delete()
        self.db.commit()
        with patch("app.services.notification_email_service.SessionLocal",side_effect=lambda:Session(self.engine)), patch("app.services.notification_email_service.send_email") as send:
            self.assertEqual(send_pending_notifications(),(0,0))
            send.assert_not_called()
        self.db.expire_all()
        self.assertEqual(self.db.scalar(select(Notification.status)),"cancelled")

    def test_full_scan_checks_old_agenda_and_replays(self):
        from scripts.sync.entity_sync import run_dataset
        self.db.execute(text("""CREATE TABLE sync_checkpoints (dataset TEXT PRIMARY KEY, last_updated_at TIMESTAMP,
            last_id BIGINT, last_run_at TIMESTAMP, status TEXT, records_processed BIGINT, records_new BIGINT,
            records_changed BIGINT, records_unchanged BIGINT, records_error BIGINT, error_message TEXT)"""))
        self.db.execute(text("INSERT INTO sync_checkpoints (dataset,last_id,status) VALUES ('agendas',100,'idle')"))
        self.db.commit()
        records=[{"id":2,"body_id":2,"meeting_id":1,"item_affair_id":2,"item_title":"Wind"},
                 {"id":1,"body_id":1,"meeting_id":1,"item_affair_id":1,"item_title":"Alter Datensatz aktualisiert"}]
        with patch("scripts.sync.entity_sync.SessionLocal",side_effect=lambda:Session(self.engine,autoflush=False)), patch("scripts.sync.entity_sync.fetch_page",return_value=records):
            run_dataset("agendas")
            run_dataset("agendas")
        self.db.expire_all()
        self.assertEqual(self.db.get(Agenda,1).item_title,"Alter Datensatz aktualisiert")
        self.assertEqual(self.count(ChangeEvent),1)
        self.assertEqual(self.count(Notification),1)

    def test_group_relations_and_details(self):
        from app.api.routes.entities import entity_detail
        self.db.add(PoliticalGroup(id=42,body_id=1,name_de="Energiekommission",updated_at=datetime(2026,1,1)))
        self.db.get(Meeting,1).group_id=42
        self.db.commit()
        self.assertEqual(related_affair_ids(self.db,"groups",self.db.get(PoliticalGroup,42)),{1,2})
        result=list_entities(self.db,"groups",category="climate",affair_id=1,canton="BE")
        self.assertEqual([item["id"] for item in result["items"]],[42])
        detail=entity_detail("groups",42,self.db)
        self.assertEqual(detail["meetings"]["pagination"]["total_items"],1)
        self.assertEqual(list_entities(self.db,"meetings",group_id=99)["items"],[])

    def test_interest_classification_notifications_person_and_no_affair(self):
        from app.api.routes.entities import entity_detail
        self.add_rule("Photovoltaik","solar_title")
        self.db.add(Person(id=77,fullname="Testperson",party_de="Testpartei"))
        self.db.commit()
        sync_record(self.db,"interests",{"id":80,"body_id":1,"person_id":77,"name_de":"Photovoltaik Verband","begin_date":datetime(2026,1,1)})
        self.db.commit()
        self.assertEqual(self.count(Notification),1)
        self.assertEqual(self.count(ChangeEventAffair),0)
        result=list_entities(self.db,"interests",category="climate",q="Photovoltaik",canton="BE",year=2026,person_id=77)
        self.assertEqual([item["id"] for item in result["items"]],[80])
        detail=entity_detail("interests",80,self.db)
        self.assertEqual(detail["person"]["fullname"],"Testperson")
        self.assertEqual(detail["affair_ids"],[])
        self.assertEqual(list_entities(self.db,"interests",affair_id=1)["items"],[])

    def test_group_watch_covers_meeting_and_agenda_changes(self):
        self.db.query(UserCategorySubscription).delete()
        self.db.add(PoliticalGroup(id=42,body_id=1,name_de="Kommission"))
        self.db.get(Meeting,1).group_id=42
        self.db.add(UserRecordWatch(user_id=1,dataset="groups",record_id=42))
        self.db.commit()
        sync_record(self.db,"meetings",{"id":1,"location":"Neuer Ort"},self.db.get(Meeting,1))
        sync_record(self.db,"agendas",{"id":1,"item_title":"Neue Traktanden"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),2)

    def test_new_endpoint_mappers_normalize_languages_nulls_dates(self):
        from scripts.sync.groups_sync import map_group
        from scripts.sync.interests_sync import map_interest
        group=map_group({"id":42,"name":{"de":"Kommission"},"type_harmonized":{"en":"Committee","de":"Kommission"},"abbreviation":None,"updated_at":"2026-01-01T01:00:00+01:00"})
        self.assertEqual(group["type_harmonized"],"committee")
        self.assertEqual(group["updated_at"],datetime(2026,1,1))
        self.assertIsNone(group["abbreviation_de"])
        interest=map_interest({"id":80,"person_id":77,"name":{"de":"Verband"},"type":{"fr":"Association"},"role_name":None,"begin_date":None})
        self.assertIsNone(interest["role_name_de"])
        self.assertEqual(interest["type_fr"],"Association")
        with self.assertRaises(ValueError):
            map_group({"id":42,"name":"invalid"})

    def test_new_dataset_sync_replays_and_ignores_timestamps(self):
        from scripts.sync.entity_sync import run_dataset
        self.db.execute(text("""CREATE TABLE sync_checkpoints (dataset TEXT PRIMARY KEY, last_updated_at TIMESTAMP,
            last_id BIGINT, last_run_at TIMESTAMP, status TEXT, records_processed BIGINT, records_new BIGINT,
            records_changed BIGINT, records_unchanged BIGINT, records_error BIGINT, error_message TEXT)"""))
        self.db.commit()
        self.add_rule("Photovoltaik","solar_title")
        for dataset in ("groups","interests"):
            record={"id":50,"body_id":1,"name":{"de":"Photovoltaik"},"updated_at":"2026-01-01"}
            with patch("scripts.sync.entity_sync.SessionLocal",side_effect=lambda:Session(self.engine,autoflush=False)), patch("scripts.sync.entity_sync.fetch_page",return_value=[record]):
                run_dataset(dataset)
                record["updated_at"]="2026-02-01"
                run_dataset(dataset)
            self.assertEqual(self.db.scalar(text("SELECT status FROM sync_checkpoints WHERE dataset=:ds"),{"ds":dataset}),"idle")
        self.assertEqual(self.count(ChangeEvent),2)
        self.assertEqual(self.count(Notification),2)

    def test_untitled_agenda_uses_meeting_and_exposes_actual_links(self):
        from app.api.routes.entities import entity_detail
        self.db.add(Agenda(id=80,body_id=1,meeting_id=1,item_number="1",item_date=datetime(2027,12,6),
                           item_url="https://example.org/meeting"))
        self.db.add(Document(source_id=500,body_id=1,agenda_id=80,name="Sitzungsunterlagen"))
        self.db.commit()
        result=list_entities(self.db,"agendas",q="Sitzung",year=2027)
        self.assertEqual(result["pagination"]["total_items"],1)
        item=result["items"][0]
        self.assertEqual(item["title"],"Sitzung")
        self.assertEqual(item["meeting"]["id"],1)
        self.assertEqual(item["source_url"],"https://example.org/meeting")
        detail=entity_detail("agendas",80,self.db)
        self.assertEqual(detail["title_origin"],"meeting")
        self.assertEqual(detail["affair_ids"],[])
        self.assertEqual(detail["documents"]["pagination"]["total_items"],1)
        self.assertEqual(entity_detail("meetings",1,self.db)["agendas"]["pagination"]["total_items"],3)

    def test_untitled_agenda_prefers_affair_and_keeps_own_title(self):
        self.db.get(Agenda,1).item_title=None
        self.db.commit()
        result=list_entities(self.db,"agendas",q="Photovoltaik")
        self.assertEqual([item["id"] for item in result["items"]],[1])
        self.assertEqual(result["items"][0]["title"],"Photovoltaik")
        self.assertEqual(result["items"][0]["title_origin"],"affair")
        self.db.get(Agenda,1).item_title="Eigener Traktandentitel"
        self.db.commit()
        result=list_entities(self.db,"agendas",affair_id=1)
        self.assertEqual(result["items"][0]["title"],"Eigener Traktandentitel")

    def test_primary_affair_subscription_includes_supporting_changes(self):
        self.db.add(UserDatasetSubscription(user_id=1,dataset="affairs"))
        self.db.commit()
        sync_record(self.db,"agendas",{"id":1,"item_title":"Änderung zum Geschäft"},self.db.get(Agenda,1))
        self.db.commit()
        self.assertEqual(self.count(Notification),1)

    def test_supporting_event_context_and_voting_details(self):
        from app.models import Event, Voting
        from app.api.routes.entities import entity_detail, available_entities
        self.db.add(Event(id=90,affair_id=1,meeting_id=1,title_de="Frist",date=datetime(2026,2,1)))
        self.db.add(Voting(id=91,affair_id=1,meeting_id=1,results_yes=12,results_no=3,results_abstention=0,decision="Angenommen"))
        self.db.commit()
        event=entity_detail("events",90,self.db)
        self.assertEqual(event["context_title"],"Photovoltaik")
        self.assertEqual(event["body"]["canton"],"BE")
        self.assertEqual(event["meeting"]["id"],1)
        meeting=entity_detail("meetings",1,self.db)
        self.assertEqual(meeting["related"]["votings"]["pagination"]["total_items"],1)
        self.assertEqual(entity_detail("votings",91,self.db)["record"]["results_abstention"],0)
        self.assertEqual(available_entities()["navigation"],["affairs","meetings","groups","interests"])

    def test_email_login_redirects_cookie_and_rejects_reuse(self):
        from app.services.email_verification_service import create_login_token
        from app.api.routes.auth import verify_login
        token=create_login_token(self.db,user_id=1)
        response=verify_login(token,self.db)
        self.assertEqual(response.status_code,303)
        self.assertEqual(response.headers["location"],"/?signed_in=1")
        self.assertIn("HttpOnly",response.headers["set-cookie"])
        self.assertEqual(verify_login(token,self.db).status_code,400)


if __name__ == "__main__":
    unittest.main()
