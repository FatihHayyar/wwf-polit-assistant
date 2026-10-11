import smtplib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.notification_content import entry, render_html
from app.services.email_service import EmailServiceError, send_email


class NotificationContentTests(unittest.TestCase):
    def test_legacy_status_uses_readable_label_and_current_value(self):
        event = SimpleNamespace(dataset='affairs', source_id=1, change_type='updated', changes=None,
                                description='Changed fields: end_date, state_name_de')
        text = entry(event, SimpleNamespace(end_date='2026-10-11', state_name_de='Beantwortet'), 'Solar')
        self.assertNotIn('Abschlussdatum:', text)
        self.assertIn('Status: Beantwortet', text)
        self.assertNotIn('Changed:', text)

    def test_html_escapes_title_and_links(self):
        markup = render_html('Dokument: <script>alert(1)</script>\nhttps://example.org/?dataset=documents&record=2')
        self.assertNotIn('<script>', markup)
        self.assertIn('&lt;script&gt;', markup)
        self.assertIn('Details in der Anwendung ansehen', markup)

    def test_smtp_response_is_preserved(self):
        with patch('app.services.email_service.settings', smtp_host='smtp.example.org', smtp_port=587,
                   smtp_from_email='sender@example.org', smtp_from_name='WWF'), \
             patch('app.services.email_service.smtplib.SMTP', side_effect=smtplib.SMTPDataError(452, b'Daily quota exceeded')):
            with self.assertRaisesRegex(EmailServiceError, 'SMTP 452: Daily quota exceeded'):
                send_email(recipient='test@example.org', subject='Test', body='Test')
