"""Create a demo affair for one user and send the resulting notification.

Usage inside the demo container:
    docker compose -f docker-compose.demo.yml exec app \
        python -m scripts.demo.send_test_notification --email name@example.org --topic renewable_electricity

Only for the demo database: the command refuses to run unless DEMO_MODE=true.
"""
import argparse
import sys

from sqlalchemy import select

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.user import User
from app.services.demo_notification_service import DEMO_TITLES, DemoNotificationError, create_demo_affair
from app.services.notification_email_service import send_pending_notifications


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--email", required=True, help="Registered and confirmed account")
    parser.add_argument("--topic", required=True, choices=sorted(DEMO_TITLES), help="Topic code of the demo affair")
    args = parser.parse_args()

    if not settings.demo_mode:
        print("DEMO_MODE is not enabled; refusing to create demo records.", file=sys.stderr)
        return 2

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.strip().lower()))
        if user is None or not user.email_verified:
            print("No confirmed account exists for this address.", file=sys.stderr)
            return 1
        try:
            result = create_demo_affair(db, user, args.topic)
        except DemoNotificationError as exc:
            db.rollback()
            print(exc, file=sys.stderr)
            return 1
        db.commit()
        user_id = user.id

    print(f"Demo affair {result.affair_id}: {result.title} ({result.canton})")
    print(f"Topics: {', '.join(result.categories)}")
    for hint in result.hints:
        print(hint)
    if result.notifications_for_user:
        sent, failed = send_pending_notifications(user_id=user_id)
        print(f"Emails sent: {sent}, failed: {failed}")
        if settings.demo_mailbox_url:
            print(f"Mailbox: {settings.demo_mailbox_url}")
        return 0 if failed == 0 else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
