"""Account and destination security checks without network access."""
import unittest
from unittest.mock import Mock, patch

from fastapi import HTTPException
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from starlette.requests import Request

import app.models
from app.api.routes.google_auth import google_callback
from app.api.routes.recipient_routes import RecipientsUpdate, update_recipients, verify_recipient
from app.db.database import Base
from app.models.notification_recipient import NotificationRecipient
from app.models.user import User
from app.services.email_service import EmailServiceError
from app.services.notification_recipient_service import send_notification_email


@compiles(BigInteger, "sqlite")
def sqlite_integer(type_, compiler, **kw):
    return "INTEGER"


class AccountPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(email="owner@example.com", is_active=True, email_verified=True)
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_new_destination_requires_verification_and_token_is_single_use(self):
        with patch("app.api.routes.recipient_routes.send_email") as send:
            result = update_recipients(RecipientsUpdate(emails=["OWNER@example.com", "other@example.com"]), self.user, self.db)
        self.assertEqual({row["email"]: row["verified"] for row in result}, {"owner@example.com": True, "other@example.com": False})
        deliver = Mock()
        send_notification_email(self.db, self.user, send_func=deliver, subject="test", body="test")
        self.assertEqual(deliver.call_args.kwargs["recipient"], "owner@example.com")
        token = send.call_args.kwargs["body"].split("token=")[1]
        verify_recipient(token, self.db)
        with self.assertRaises(HTTPException):
            verify_recipient(token, self.db)
        deliver.reset_mock()
        send_notification_email(self.db, self.user, send_func=deliver, subject="test", body="test")
        self.assertEqual(deliver.call_count, 2)

    def test_pending_destinations_do_not_fall_back_to_login_email(self):
        self.db.add(NotificationRecipient(user_id=self.user.id, email="pending@example.com", verified=False))
        self.db.commit()
        send = Mock()
        with self.assertRaises(EmailServiceError):
            send_notification_email(self.db, self.user, send_func=send)
        send.assert_not_called()

    def test_google_callback_rejects_state_before_network_or_account_changes(self):
        request = Request({"type": "http", "headers": [(b"cookie", b"google_oauth_state=expected")]})
        with patch("app.api.routes.google_auth.httpx.Client") as client:
            with self.assertRaises(HTTPException) as error:
                google_callback(request, state="wrong", code="code", db=self.db)
        self.assertEqual(error.exception.status_code, 400)
        client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
