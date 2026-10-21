"""HTTP-level checks for authentication, abuse protection and the demo flow.

The tests run the real FastAPI application against an isolated SQLite
database. Emails are captured instead of being sent.
"""
import re
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers all tables on Base.metadata)
from app.core.config import settings
from app.core.rate_limit import Limit, limiter
from app.db.database import Base, get_db
from app.main import app as fastapi_app
from app.models.classification import ClassificationCategory
from app.models.entities import Affair, Body
from app.models.notification import Notification
from app.models.subscription import UserCantonSubscription, UserCategorySubscription
from app.models.user import User
from app.services.demo_notification_service import DEMO_TITLES
from scripts.seed_classification import seed_taxonomy


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)

        def override_db():
            with self.Session() as db:
                yield db

        fastapi_app.dependency_overrides[get_db] = override_db
        limiter.reset()
        self.mails = []
        mail_patch = patch("app.api.routes.auth.send_email",
                           side_effect=lambda **mail: self.mails.append(mail))
        mail_patch.start()
        self.addCleanup(mail_patch.stop)
        self.client = TestClient(fastapi_app)

    def tearDown(self):
        fastapi_app.dependency_overrides.clear()
        self.engine.dispose()

    def add_user(self, email="owner@example.com", verified=True):
        with self.Session() as db:
            user = User(email=email, is_active=True, email_verified=verified)
            db.add(user)
            db.commit()
            return user.id

    def link_token(self, mail):
        return re.search(r"token=([\w-]+)", mail["body"]).group(1)

    def sign_in(self, email="owner@example.com"):
        self.client.post("/api/v1/auth/login", json={"email": email})
        token = self.link_token(self.mails[-1])
        response = self.client.post("/api/v1/auth/verify-login", data={"token": token}, follow_redirects=False)
        self.assertEqual(response.status_code, 303)
        return response


class AccountEnumerationTests(ApiTestCase):
    def test_register_and_login_answer_identically_for_known_and_unknown_addresses(self):
        self.add_user("known@example.com")
        answers = set()
        for path in ("register", "login"):
            for email in ("known@example.com", "unknown@example.com"):
                limiter.reset()
                response = self.client.post(f"/api/v1/auth/{path}", json={"email": email})
                self.assertEqual(response.status_code, 200)
                answers.add(response.text)
        self.assertEqual(len(answers), 1)

    def test_login_for_unknown_address_sends_no_email(self):
        self.client.post("/api/v1/auth/login", json={"email": "nobody@example.com"})
        self.assertEqual(self.mails, [])

    def test_register_for_existing_account_sends_login_link_instead(self):
        self.add_user("known@example.com")
        self.client.post("/api/v1/auth/register", json={"email": "known@example.com"})
        self.assertEqual(len(self.mails), 1)
        self.assertIn("/api/v1/auth/verify-login?token=", self.mails[0]["body"])

    def test_login_for_unverified_account_resends_verification(self):
        self.add_user("pending@example.com", verified=False)
        self.client.post("/api/v1/auth/login", json={"email": "pending@example.com"})
        self.assertIn("/api/v1/auth/verify-email?token=", self.mails[0]["body"])


class RateLimitTests(ApiTestCase):
    def test_second_email_to_same_address_within_cooldown_is_rejected(self):
        first = self.client.post("/api/v1/auth/register", json={"email": "new@example.com"})
        second = self.client.post("/api/v1/auth/register", json={"email": "new@example.com"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
        self.assertGreater(int(second.headers["retry-after"]), 0)
        self.assertEqual(len(self.mails), 1)

    def test_one_client_cannot_mail_many_addresses(self):
        codes = [self.client.post("/api/v1/auth/register", json={"email": f"user{i}@example.com"}).status_code
                 for i in range(12)]
        self.assertEqual(codes[:10], [200] * 10)
        self.assertEqual(codes[10:], [429, 429])
        self.assertEqual(len(self.mails), 10)

    def test_limits_can_be_disabled_for_controlled_environments(self):
        with patch.object(settings, "rate_limit_enabled", False):
            codes = {self.client.post("/api/v1/auth/login", json={"email": "a@example.com"}).status_code
                     for _ in range(3)}
        self.assertEqual(codes, {200})

    def test_subscription_confirmation_emails_are_capped_without_blocking_saves(self):
        self.add_user()
        self.sign_in()
        with patch("app.api.routes.subscriptions.send_email") as send, \
                patch("app.api.routes.subscriptions.SUBSCRIPTION_CHANGE_PER_USER", Limit(2, 3600)):
            codes = [self.client.put("/api/v1/subscriptions", json={"canton_keys": ["BE"]}).status_code
                     for _ in range(4)]
        self.assertEqual(codes, [200] * 4)
        self.assertEqual(send.call_count, 2)


class EmailLinkTests(ApiTestCase):
    def test_opening_a_link_does_not_consume_the_token(self):
        self.add_user()
        self.client.post("/api/v1/auth/login", json={"email": "owner@example.com"})
        token = self.link_token(self.mails[0])
        for _ in range(3):
            page = self.client.get(f"/api/v1/auth/verify-login?token={token}")
            self.assertEqual(page.status_code, 200)
            self.assertIn('method="post"', page.text)
        confirmed = self.client.post("/api/v1/auth/verify-login", data={"token": token}, follow_redirects=False)
        self.assertEqual(confirmed.status_code, 303)
        self.assertIn("httponly", confirmed.headers["set-cookie"].lower())
        reused = self.client.post("/api/v1/auth/verify-login", data={"token": token}, follow_redirects=False)
        self.assertEqual(reused.status_code, 400)

    def test_registration_link_verifies_and_signs_in(self):
        self.client.post("/api/v1/auth/register", json={"email": "fresh@example.com"})
        token = self.link_token(self.mails[0])
        self.client.post("/api/v1/auth/verify-email", data={"token": token}, follow_redirects=False)
        me = self.client.get("/api/v1/auth/me")
        self.assertEqual(me.json(), {"email": "fresh@example.com", "email_verified": True})

    def test_token_is_escaped_in_confirmation_page(self):
        page = self.client.get('/api/v1/auth/verify-login?token="><script>alert(1)</script>')
        self.assertNotIn("<script>alert", page.text)

    def test_cross_site_confirmation_is_rejected(self):
        self.add_user()
        self.client.post("/api/v1/auth/login", json={"email": "owner@example.com"})
        token = self.link_token(self.mails[0])
        response = self.client.post("/api/v1/auth/verify-login", data={"token": token},
                                    headers={"Origin": "https://attacker.example"}, follow_redirects=False)
        self.assertEqual(response.status_code, 403)
        same_site = self.client.post("/api/v1/auth/verify-login", data={"token": token},
                                     headers={"Origin": settings.verification_base_url}, follow_redirects=False)
        self.assertEqual(same_site.status_code, 303)


class SessionTests(ApiTestCase):
    def test_logout_revokes_previously_issued_tokens(self):
        self.add_user()
        self.sign_in()
        stolen = self.client.cookies.get("access_token")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/logout").status_code, 204)
        replay = self.client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {stolen}"})
        self.assertEqual(replay.status_code, 401)

    def test_new_sign_in_after_logout_works(self):
        self.add_user()
        self.sign_in()
        self.client.post("/api/v1/auth/logout")
        limiter.reset()
        self.sign_in()
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)

    def test_subscriptions_require_authentication(self):
        self.assertEqual(self.client.get("/api/v1/subscriptions").status_code, 401)
        self.assertEqual(self.client.put("/api/v1/subscriptions", json={}).status_code, 401)


class SecurityHeaderTests(ApiTestCase):
    def test_frontend_sends_strict_headers(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])
        self.assertIn("script-src 'self'", response.headers["content-security-policy"])
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["referrer-policy"], "same-origin")

    def test_frontend_assets_are_versioned(self):
        html = self.client.get("/").text
        for match in re.findall(r'/assets/([\w.-]+\.(?:js|css))"', html):
            self.fail(f"Unversioned asset reference: {match}")
        self.assertRegex(html, r'/assets/app\.js\?v=[0-9a-f]{12}"')

    def test_frontend_has_no_inline_code_blocked_by_the_policy(self):
        html = self.client.get("/").text
        self.assertNotRegex(html, r"<script(?![^>]*\bsrc=)[^>]*>")
        self.assertNotIn(" style=", html)
        self.assertNotRegex(html, r"\son[a-z]+=")

    def test_api_documentation_still_loads(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("content-security-policy", response.headers)


class RecipientLinkTests(ApiTestCase):
    def test_recipient_confirmation_uses_post_and_is_single_use(self):
        self.add_user()
        self.sign_in()
        with patch("app.api.routes.recipient_routes.send_email") as send:
            self.client.put("/api/v1/subscriptions/recipients",
                            json={"emails": ["owner@example.com", "team@example.com"]})
        token = send.call_args.kwargs["body"].split("token=")[1]
        self.assertEqual(self.client.get(f"/api/v1/subscriptions/recipients/verify?token={token}").status_code, 200)
        first = self.client.post("/api/v1/subscriptions/recipients/verify", data={"token": token}, follow_redirects=False)
        second = self.client.post("/api/v1/subscriptions/recipients/verify", data={"token": token}, follow_redirects=False)
        self.assertEqual((first.status_code, second.status_code), (303, 400))

    def test_recipient_updates_are_limited_per_user(self):
        self.add_user()
        self.sign_in()
        with patch("app.api.routes.recipient_routes.send_email"):
            codes = [self.client.put("/api/v1/subscriptions/recipients", json={"emails": ["owner@example.com"]}).status_code
                     for _ in range(11)]
        self.assertEqual(codes[-1], 429)
        self.assertEqual(codes[:10], [200] * 10)


class DemoNotificationTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        with self.Session() as db:
            seed_taxonomy(db)
            db.add_all([Body(id=1, canton_key="BE", body_key="BE", name_de="Grosser Rat Bern"),
                        Body(id=2, canton_key="ZH", body_key="ZH", name_de="Kantonsrat Zürich")])
            db.commit()
        self.sent = []
        for target in ("app.services.notification_email_service.SessionLocal",):
            session_patch = patch(target, self.Session)
            session_patch.start()
            self.addCleanup(session_patch.stop)
        send_patch = patch("app.services.notification_email_service.send_email",
                           side_effect=lambda **mail: self.sent.append(mail))
        send_patch.start()
        self.addCleanup(send_patch.stop)

    def subscribe(self, topic_code, cantons=()):
        with self.Session() as db:
            user_id = db.scalar(select(User.id).where(User.email == "owner@example.com"))
            category_id = db.scalar(select(ClassificationCategory.id).where(ClassificationCategory.code == topic_code))
            db.add(UserCategorySubscription(user_id=user_id, category_id=category_id))
            for canton in cantons:
                db.add(UserCantonSubscription(user_id=user_id, canton_key=canton))
            db.commit()

    def test_demo_endpoints_are_hidden_outside_demo_mode(self):
        self.add_user()
        self.sign_in()
        self.assertEqual(self.client.get("/api/v1/demo/status").json(), {"enabled": False, "mailbox_url": None})
        response = self.client.post("/api/v1/demo/notifications", json={"category_code": "forest"})
        self.assertEqual(response.status_code, 404)

    def test_subscribed_topic_produces_a_notification_email(self):
        self.add_user()
        self.subscribe("climate_energy", cantons=["ZH"])
        self.sign_in()
        with patch.object(settings, "demo_mode", True), patch.object(settings, "demo_mailbox_url", "http://localhost:8025"):
            topics = self.client.get("/api/v1/demo/topics").json()
            self.assertEqual(topics["preselected"], "renewable_electricity")
            response = self.client.post("/api/v1/demo/notifications", json={"category_code": topics["preselected"]})
        self.assertEqual(response.status_code, 201, response.text)
        result = response.json()
        self.assertEqual(result["canton"], "ZH")
        self.assertEqual(result["notifications_for_user"], 1)
        self.assertEqual((result["emails_sent"], result["emails_failed"]), (1, 0))
        self.assertEqual(result["mailbox_url"], "http://localhost:8025")
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0]["recipient"], "owner@example.com")
        self.assertIn("Photovoltaik", self.sent[0]["body"])
        with self.Session() as db:
            self.assertEqual(db.scalar(select(Notification.status)), "sent")
            self.assertGreaterEqual(db.get(Affair, result["affair_id"]).id, 900_000_000)

    def test_unmatched_subscription_explains_instead_of_sending(self):
        self.add_user()
        self.subscribe("forest")
        self.sign_in()
        with patch.object(settings, "demo_mode", True):
            response = self.client.post("/api/v1/demo/notifications", json={"category_code": "renewable_electricity"})
        result = response.json()
        self.assertEqual(result["notifications_for_user"], 0)
        self.assertTrue(result["hints"])
        self.assertEqual(self.sent, [])

    def test_demo_notifications_are_rate_limited(self):
        self.add_user()
        self.subscribe("forest")
        self.sign_in()
        with patch.object(settings, "demo_mode", True):
            codes = [self.client.post("/api/v1/demo/notifications", json={"category_code": "forest"}).status_code
                     for _ in range(6)]
        self.assertEqual(codes, [201] * 5 + [429])

    def test_every_demo_title_is_classified_into_its_topic(self):
        with self.Session() as db:
            from app.classification.classifier import AffairClassifier
            classifier = AffairClassifier(db)
            codes = {category.id: category.code for category in db.scalars(select(ClassificationCategory))}
            for code, title in DEMO_TITLES.items():
                with self.subTest(code=code):
                    affair = Affair(id=1, title_de=title)
                    found = {codes[match.category_id] for match in classifier.accepted_title_matches(affair)}
                    self.assertIn(code, found)


if __name__ == "__main__":
    unittest.main()
