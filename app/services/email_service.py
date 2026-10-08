from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailServiceError(RuntimeError):
    """Raised when an email cannot be sent."""


def send_email(
    *,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    if not settings.smtp_host:
        raise EmailServiceError("SMTP_HOST is not configured.")

    if not settings.smtp_from_email:
        raise EmailServiceError("SMTP_FROM_EMAIL is not configured.")

    message = EmailMessage()
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    )
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            if settings.smtp_username and settings.smtp_password:
                smtp.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            smtp.send_message(message)

    except (OSError, smtplib.SMTPException) as exc:
        raise EmailServiceError(
            "Could not send email."
        ) from exc