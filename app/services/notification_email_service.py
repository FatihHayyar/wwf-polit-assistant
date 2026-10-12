from __future__ import annotations
from app.services.notification_recipient_service import has_verified_destination, send_notification_email

from datetime import datetime, timezone

from sqlalchemy import case, func, select

from app.db.database import SessionLocal
from app.models.change_event import ChangeEvent
from app.models.change_event_affair import ChangeEventAffair
from app.models.dataset_subscription import UserDatasetSubscription
from app.core.config import settings
from app.models.entities import Affair, Body
from app.models.notification import Notification
from app.models.subscription import (
    UserCategorySubscription,
    UserCantonSubscription,
)
from app.models.user import User
from app.services.email_service import (
    EmailServiceError,
    send_email,
)
from app.services.notification_service import (
    get_category_and_ancestor_ids,
)


def user_still_subscribed(db, user_id: int, affair: Affair) -> bool:
    category_ids = set(
        db.scalars(
            select(UserCategorySubscription.category_id).where(
                UserCategorySubscription.user_id == user_id
            )
        ).all()
    )

    canton_keys = set(
        db.scalars(
            select(UserCantonSubscription.canton_key).where(
                UserCantonSubscription.user_id == user_id
            )
        ).all()
    )

    # Both empty means no active notification subscription.
    if not category_ids and not canton_keys:
        return False

    # Empty category selection means all themes.
    if category_ids:
        affair_category_ids = get_category_and_ancestor_ids(
            db,
            affair.id,
        )

        if not category_ids.intersection(affair_category_ids):
            return False

    # Empty canton selection means all cantons.
    if canton_keys:
        if affair.body_id is None:
            return False

        canton_key = db.scalar(
            select(Body.canton_key).where(
                Body.id == affair.body_id
            )
        )

        if (
            canton_key is None
            or canton_key.strip().upper() not in canton_keys
        ):
            return False

    return True


def send_pending_individual_notifications(
    *,
    limit: int | None = None,
    batch_size: int = 100,
    before_each=None,
    on_progress=None,
) -> tuple[int, int]:
    """
    Send pending notification emails.

    Returns (sent_count, failed_count).

    Failed notifications remain pending for retry.
    Cancelled notifications are not sent.
    """

    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    sent_count = 0
    failed_count = 0

    with SessionLocal() as db:
        upper_id = db.scalar(select(func.max(Notification.id)).where(Notification.status == "pending")) or 0

    def pending_ids():
        cursor = 0
        attempted = 0
        while cursor < upper_id and (limit is None or attempted < limit):
            size = batch_size if limit is None else min(batch_size, limit - attempted)
            with SessionLocal() as db:
                ids = db.scalars(select(Notification.id).where(
                    Notification.status == "pending", Notification.id > cursor,
                    Notification.id <= upper_id).order_by(Notification.id).limit(size)).all()
            if not ids:
                break
            cursor = ids[-1]
            attempted += len(ids)
            yield from ids

    for notification_id in pending_ids():
        if on_progress is not None:
            on_progress(sent_count, failed_count)
        if before_each is not None:
            before_each()
        with SessionLocal() as db:
            notification = db.scalar(select(Notification).where(Notification.id == notification_id)
                                     .with_for_update(skip_locked=True))

            if (
                notification is None
                or notification.status != "pending"
            ):
                continue

            user = db.get(User, notification.user_id)
            if user and not has_verified_destination(db, user):
                continue
            event = db.get(
                ChangeEvent,
                notification.change_event_id,
            )

            if (
                user is None
                or not user.is_active
                or not user.email_verified
                or event is None
                or event.change_type == "ignored"
            ):
                notification.status = "cancelled"
                db.commit()
                continue
            from app.services.notification_policy import event_eligible
            if not event_eligible(event):
                notification.status = "cancelled"
                notification.error_message = "No meaningful change under current notification policy."
                db.commit()
                continue

            from app.services.monitoring_match_service import event_subjects, matching_subject
            subject = matching_subject(db, user.id, event.dataset, event_subjects(db, event))
            if subject is None:
                notification.status = "cancelled"
                db.commit()
                continue
            from app.services.entity_registry import ENTITIES
            from app.services.entity_relations import entity_key
            spec = ENTITIES[event.dataset]
            source_entity = db.get(spec.model, event.source_id)
            title = next((getattr(source_entity, field) for field in spec.title_fields
                          if source_entity is not None and getattr(source_entity, field)),
                         f"{event.dataset} {event.source_id}")
            title = " ".join(title.split())[:500]

            action = f"{event.dataset}: " + ("New record" if event.change_type == "created" else "Record updated")

            body = (
                f"{action}\n\n"
                f"{title}\n\n"
                f"Related affair: {event.affair_id or '?'}\n"
                f"Dataset: {event.dataset}\n"
                f"Record: {event.source_id}\n"
                f"{event.description or ''}\n\n"
                f"{settings.verification_base_url}/?dataset={event.dataset}&record={event.source_id}\n"
            )

            try:
                send_notification_email(
                    db, user, send_func=send_email,
                    subject=f"WWF Polit-Assistant: {action}",
                    body=body,
                )
            except EmailServiceError as exc:
                notification.error_message = str(exc)
                db.commit()
                failed_count += 1
                continue

            notification.status = "sent"
            notification.sent_at = datetime.now(timezone.utc)
            notification.error_message = None
            db.commit()

            sent_count += 1

    if on_progress is not None:
        on_progress(sent_count, failed_count)
    return sent_count, failed_count


def send_pending_notifications(*, limit=None, batch_size=100, before_each=None, on_progress=None, digest=True):
    """Send one summary per user/affair (or standalone record), without a total cap."""
    if not digest:
        return send_pending_individual_notifications(limit=limit,batch_size=batch_size,before_each=before_each,on_progress=on_progress)
    if batch_size < 1 or (limit is not None and limit < 1):
        raise ValueError("limits must be positive")
    from app.services.notification_policy import event_eligible
    from app.services.notification_content import NAMES, entry, render_html
    from app.services.monitoring_match_service import event_subjects, matching_subject
    from app.services.entity_registry import ENTITIES
    standalone_dataset=case((ChangeEvent.affair_id.is_(None),ChangeEvent.dataset),else_=None)
    standalone_id=case((ChangeEvent.affair_id.is_(None),ChangeEvent.source_id),else_=None)
    with SessionLocal() as db:
        upper=db.scalar(select(func.max(Notification.id)).where(Notification.status=="pending")) or 0
    cursor=0;sent=failed=attempted=0
    consecutive_failures = 0
    while cursor < upper and (limit is None or attempted < limit):
        with SessionLocal() as db:
            groups=db.execute(select(Notification.user_id,ChangeEvent.affair_id,standalone_dataset.label("dataset"),
                standalone_id.label("record_id"),func.min(Notification.id).label("first_id"))
                .join(ChangeEvent,ChangeEvent.id==Notification.change_event_id)
                .where(Notification.status=="pending",Notification.id<=upper)
                .group_by(Notification.user_id,ChangeEvent.affair_id,standalone_dataset,standalone_id)
                .having(func.min(Notification.id)>cursor).order_by(func.min(Notification.id)).limit(batch_size)).all()
        if not groups:break
        for group in groups:
            if limit is not None and attempted>=limit:break
            if on_progress:on_progress(sent,failed)
            if before_each:before_each()
            cursor=group.first_id;attempted+=1
            with SessionLocal() as db:
                query=select(Notification).join(ChangeEvent,ChangeEvent.id==Notification.change_event_id).where(
                    Notification.status=="pending",Notification.id<=upper,Notification.user_id==group.user_id)
                if group.affair_id is not None:query=query.where(ChangeEvent.affair_id==group.affair_id)
                else:query=query.where(ChangeEvent.affair_id.is_(None),ChangeEvent.dataset==group.dataset,ChangeEvent.source_id==group.record_id)
                notifications=db.scalars(query.order_by(Notification.id).with_for_update(skip_locked=True,of=Notification)).all()
                user=db.get(User,group.user_id);deliver=[];lines=[]
                if user and not has_verified_destination(db, user):
                    continue
                for notification in notifications:
                    event=db.get(ChangeEvent,notification.change_event_id)
                    if not user or not user.is_active or not user.email_verified or not event or not event_eligible(event) or matching_subject(db,user.id,event.dataset,event_subjects(db,event)) is None:
                        notification.status="cancelled";notification.error_message="No longer eligible under notification policy/subscription."
                        continue
                    deliver.append(notification)
                    if len(lines)<30:
                        entity=db.get(ENTITIES[event.dataset].model,event.source_id)
                        title=next((getattr(entity,f) for f in ENTITIES[event.dataset].title_fields if entity is not None and getattr(entity,f,None)),event.dataset)
                        title=" ".join(title.split())[:250]
                        lines.append(entry(event, entity, title))
                if not deliver:db.commit();continue
                dataset="affairs" if group.affair_id is not None else group.dataset
                record_id=group.affair_id if group.affair_id is not None else group.record_id
                entity=db.get(ENTITIES[dataset].model,record_id)
                title=next((getattr(entity,f) for f in ENTITIES[dataset].title_fields if entity is not None and getattr(entity,f,None)),dataset)
                title=" ".join(title.split())[:200]
                kinds = sorted({NAMES.get(db.get(ChangeEvent, n.change_event_id).dataset, "Inhalt") for n in deliver})
                body=f"{len(deliver)} Neuigkeiten zu: {title}\nBereiche: {', '.join(kinds)}\n\n"+"\n\n".join(lines)
                if len(deliver)>len(lines):body+=f"\n\n{len(deliver)-len(lines)} weitere ?nderungen finden Sie im ?nderungsverlauf des Eintrags."
                main_url = f"{settings.verification_base_url.rstrip('/')}/?dataset={dataset}&record={record_id}"
                if not any(main_url in line.splitlines() for line in lines):
                    body += f"\n\n{main_url}"
                body += "\n\nSie erhalten diese Nachricht aufgrund Ihrer Abonnements. Diese k?nnen Sie in der Anwendung verwalten."
                try:send_notification_email(db,user,send_func=send_email,subject=f"WWF: {', '.join(kinds)} ? {title}",body=body,html_body=render_html(body))
                except EmailServiceError as exc:
                    for notification in deliver:notification.error_message=str(exc)
                    failed+=1
                    consecutive_failures += 1
                else:
                    for notification in deliver:
                        notification.status="sent";notification.sent_at=datetime.now(timezone.utc);notification.error_message=None
                    sent+=1
                    consecutive_failures = 0
                db.commit()
                if consecutive_failures >= 3:
                    if on_progress: on_progress(sent, failed)
                    raise EmailServiceError(f"Email delivery stopped after 3 consecutive failures: {deliver[0].error_message}")
    if on_progress:on_progress(sent,failed)
    return sent,failed
