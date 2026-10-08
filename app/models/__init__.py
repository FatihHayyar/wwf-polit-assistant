
from sqlalchemy import Index

from app.models.change_event import ChangeEvent
from app.models.classification import (
    AffairClassification,
    ClassificationCategory,
    ClassificationEvidence,
    ClassificationRule,
)
from app.models.email_token import EmailToken
from app.models.entities import (
    Agenda,
    Affair,
    Body,
    Document,
    Event,
    Interest,
    Meeting,
    Membership,
    ParliamentaryText,
    Person,
    PoliticalGroup,
    Voting,
)
from app.models.notification import Notification
from app.models.subscription import (
    UserCantonSubscription,
    UserCategorySubscription,
)
from app.models.user import User


# Bodies
Index("idx_bodies_body_key", Body.body_key)
Index("idx_bodies_canton_key", Body.canton_key)

# Affairs
Index("idx_affairs_body_id", Affair.body_id)
Index("idx_affairs_begin_date", Affair.begin_date)
Index("idx_affairs_created_at", Affair.created_at)
Index("idx_affairs_updated_at", Affair.updated_at)
Index("idx_affairs_active", Affair.active)

# Persons
Index("idx_persons_body_id", Person.body_id)

# Groups
Index("idx_groups_body_id", PoliticalGroup.body_id)

# Memberships
Index("idx_memberships_person_id", Membership.person_id)
Index("idx_memberships_group_id", Membership.group_id)

# Interests
Index("idx_interests_person_id", Interest.person_id)

# Meetings
Index("idx_meetings_body_id", Meeting.body_id)
Index("idx_meetings_begin_date", Meeting.begin_date)
Index("idx_meetings_updated_at", Meeting.updated_at)

# Agendas
Index("idx_agendas_meeting_id", Agenda.meeting_id)
Index("idx_agendas_affair_id", Agenda.item_affair_id)
Index("idx_agendas_item_date", Agenda.item_date)

# Events
Index("idx_events_affair_id", Event.affair_id)
Index("idx_events_meeting_id", Event.meeting_id)
Index("idx_events_date", Event.date)

# Votings
Index("idx_votings_affair_id", Voting.affair_id)
Index("idx_votings_meeting_id", Voting.meeting_id)
Index("idx_votings_date", Voting.date)

# Documents
Index("idx_documents_source_id", Document.source_id)
Index("idx_documents_body_id", Document.body_id)
Index("idx_documents_affair_id", Document.affair_id)
Index("idx_documents_agenda_id", Document.agenda_id)
Index("idx_documents_meeting_id", Document.meeting_id)
Index("idx_documents_hash", Document.hash)

# Texts
Index("idx_texts_body_id", ParliamentaryText.body_id)
Index("idx_texts_affair_id", ParliamentaryText.affair_id)
Index("idx_texts_text_date", ParliamentaryText.text_date)


__all__ = [
    "Agenda",
    "Affair",
    "AffairClassification",
    "Body",
    "ChangeEvent",
    "ClassificationCategory",
    "ClassificationEvidence",
    "ClassificationRule",
    "Document",
    "EmailToken",
    "Event",
    "Interest",
    "Meeting",
    "Membership",
    "Notification",
    "ParliamentaryText",
    "Person",
    "PoliticalGroup",
    "User",
    "UserCantonSubscription",
    "UserCategorySubscription",
    "Voting",
]
