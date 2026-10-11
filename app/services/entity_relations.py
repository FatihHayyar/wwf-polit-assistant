"""Resolve direct and agenda/meeting-mediated affair relationships."""
from sqlalchemy import select, union, or_, and_, false
from sqlalchemy.orm import Session

from app.models.entities import Agenda, Affair, Document, Event, Meeting, ParliamentaryText, Voting


def related_affair_selects(dataset: str, entity):
    if dataset == "interests":
        # A person's declared interest is not itself a parliamentary affair.
        return [select(Affair.id).where(false())]
    if dataset == "groups":
        meetings = select(Meeting.id).where(Meeting.group_id == entity.id)
        return [select(getattr(link, field)).where(link.meeting_id.in_(meetings))
                for link, field in ((Agenda,"item_affair_id"),(Event,"affair_id"),(Voting,"affair_id"),(Document,"affair_id"))]
    if dataset == "affairs":
        return [select(Affair.id).where(Affair.id == entity.id)]
    if dataset == "agendas":
        return [select(Affair.id).where(Affair.id == entity.item_affair_id)]
    if dataset == "meetings":
        return [
            select(Agenda.item_affair_id).where(Agenda.meeting_id == entity.id),
            select(Event.affair_id).where(Event.meeting_id == entity.id),
            select(Voting.affair_id).where(Voting.meeting_id == entity.id),
            select(Document.affair_id).where(Document.meeting_id == entity.id),
        ]
    queries = [select(Affair.id).where(Affair.id == entity.affair_id)]
    missing_affair = entity.affair_id.is_(None) if hasattr(entity.affair_id, "is_") else entity.affair_id is None
    if dataset == "documents":
        queries.append(select(Agenda.item_affair_id).where(Agenda.id == entity.agenda_id, missing_affair))
    if dataset in {"documents", "events", "votings"}:
        missing_agenda = (entity.agenda_id.is_(None) if hasattr(entity.agenda_id, "is_") else entity.agenda_id is None) if dataset == "documents" else True
        queries.append(select(Agenda.item_affair_id).where(Agenda.meeting_id == entity.meeting_id, missing_affair, missing_agenda))
    return queries


def related_affair_ids(db: Session, dataset: str, entity) -> set[int]:
    queries = related_affair_selects(dataset, entity)
    query = union(*queries) if len(queries) > 1 else queries[0]
    ids = {value for value in db.scalars(query) if value is not None}
    if not ids:
        return set()
    return set(db.scalars(select(Affair.id).where(Affair.id.in_(ids))))


def correlated_affair_ids(dataset: str, model):
    # Explicit correlation keeps the entity in the outer query rather than
    # accidentally selecting relationships for every entity in the database.
    queries = [query.correlate(model) for query in related_affair_selects(dataset, model)]
    return union(*queries) if len(queries) > 1 else queries[0]


def entity_key(dataset: str, entity) -> int:
    return entity.pk if dataset == "documents" else entity.id


def related_entity_condition(dataset, model, affair_ids):
    """Invert relationships so list/count queries can use indexed IDs."""
    if dataset == "affairs":
        return model.id.in_(affair_ids)
    if dataset == "interests":
        return false()
    if dataset == "groups":
        return model.id.in_(select(Meeting.group_id).where(related_entity_condition("meetings", Meeting, affair_ids)))
    if dataset == "agendas":
        return model.item_affair_id.in_(affair_ids)
    if dataset == "meetings":
        queries = [select(link.meeting_id).where(getattr(link, field).in_(affair_ids))
                   for link, field in ((Agenda,"item_affair_id"),(Event,"affair_id"),(Voting,"affair_id"),(Document,"affair_id"))]
        return model.id.in_(union(*queries))
    direct = model.affair_id.in_(affair_ids)
    if dataset == "texts":
        return direct
    meetings = select(Agenda.meeting_id).where(Agenda.item_affair_id.in_(affair_ids))
    if dataset == "documents":
        agendas = select(Agenda.id).where(Agenda.item_affair_id.in_(affair_ids))
        return or_(direct, and_(model.affair_id.is_(None), model.agenda_id.in_(agendas)),
                   and_(model.affair_id.is_(None), model.agenda_id.is_(None), model.meeting_id.in_(meetings)))
    return or_(direct, and_(model.affair_id.is_(None), model.meeting_id.in_(meetings)))
