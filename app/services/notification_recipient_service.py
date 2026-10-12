from app.models.notification_recipient import NotificationRecipient
from app.services.email_service import EmailServiceError, send_email


def has_verified_destination(db, user):
    recipients = db.query(NotificationRecipient).filter_by(user_id=user.id).all()
    return not recipients or any(row.verified for row in recipients)


def send_notification_email(db, user, send_func=send_email, **message):
    recipients = db.query(NotificationRecipient).filter_by(user_id=user.id).all()
    # Existing accounts keep receiving mail until they explicitly choose destinations.
    addresses = [row.email for row in recipients if row.verified] if recipients else [user.email]
    if not addresses:
        raise EmailServiceError("No verified notification destination available.")
    for address in addresses:
        send_func(recipient=address, **message)
