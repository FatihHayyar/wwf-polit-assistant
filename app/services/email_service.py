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
    html_body: str | None = None,
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
    if html_body is not None:
        message.add_alternative(html_body, subtype="html")

    stage = "connect"
    try:
        with smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        ) as smtp:
            stage = "TLS"
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            if settings.smtp_username and settings.smtp_password:
                stage = "authentication"
                smtp.login(
                    settings.smtp_username,
                    settings.smtp_password,
                )

            stage = "delivery"
            smtp.send_message(message)

    except (OSError, smtplib.SMTPException) as exc:
        if isinstance(exc, smtplib.SMTPResponseException):
            detail = exc.smtp_error.decode("utf-8", errors="replace") if isinstance(exc.smtp_error, bytes) else str(exc.smtp_error)
            reason = f"SMTP {exc.smtp_code}: {detail}"
        elif isinstance(exc, smtplib.SMTPRecipientsRefused):
            reason = "SMTP rejected the recipient."
        else:
            reason = f"SMTP {stage} failed ({type(exc).__name__}): {str(exc)[:300]}"
        raise EmailServiceError(reason) from exc