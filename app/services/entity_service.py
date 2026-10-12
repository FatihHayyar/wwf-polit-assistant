from datetime import date, datetime, time, timedelta
from math import ceil

from fastapi.encoders import jsonable_encoder
from sqlalchemy import exists, extract, func, or_, select

from app.models.change_event import ChangeEvent
from app.models.change_event_affair import ChangeEventAffair
from app.models.classification import AffairClassification, ClassificationCategory
from app.models.entity_classification import EntityClassification
from app.models.entities import Affair, Body, Meeting, Agenda, PoliticalGroup, Person
from app.services.entity_registry import ENTITIES
from app.services.entity_relations import entity_key, related_affair_ids, related_entity_condition


def category_ids(db, code):
    root = db.scalar(select(ClassificationCategory.id).where(ClassificationCategory.code == code))
    if root is None:
        return set()
    result, pending = {root}, {root}
    while pending:
        children = set(db.scalars(select(ClassificationCategory.id).where(ClassificationCategory.parent_id.in_(pending)))) - result
        result |= children
        pending = children
    return result


def search_expression(dataset):
    spec = ENTITIES[dataset]
    parts = [func.coalesce(getattr(spec.model, field), "") for field in spec.title_fields]
    expression = parts[0]
    for part in parts[1:]:
        expression = expression + "\n" + part
    return func.lower(expression)


def entity_statement(db, dataset, *, q=None, canton=None, category=None, subcategory=None,
                     year=None, month=None, date_from=None, date_to=None, affair_id=None,
                     group_id=None, person_id=None, agenda_id=None, meeting_id=None, direct_search=False):
    spec = ENTITIES[dataset]
    model = spec.model
    key = model.pk if dataset == "documents" else model.id
    statement = select(model)
    if agenda_id is not None:
        statement = statement.where(model.agenda_id == agenda_id) if dataset == "documents" else statement.where(False)
    if meeting_id is not None:
        statement = statement.where(model.meeting_id == meeting_id) if dataset in {"agendas","events","votings","documents"} else statement.where(False)
    if group_id is not None:
        statement = statement.where(model.group_id == group_id) if dataset == "meetings" else statement.where(False)
    if person_id is not None:
        statement = statement.where(model.person_id == person_id) if dataset == "interests" else statement.where(False)
    if q and q.strip():
        term = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        matches = [search_expression(dataset).like(term.lower(), escape="\\")] if direct_search else [getattr(model, field).ilike(term, escape="\\") for field in spec.title_fields]
        if direct_search and dataset in {"documents", "texts"} and db.bind.dialect.name == "postgresql":
            from sqlalchemy import literal_column
            config = literal_column("'simple'::regconfig")
            matches = [func.to_tsvector(config, func.left(search_expression(dataset), 100000)).op("@@")(func.plainto_tsquery(config, q.strip()))]

        if dataset == "agendas" and not direct_search:
            matches.extend([
                model.meeting_id.in_(select(Meeting.id).where(or_(*(getattr(Meeting, field).ilike(term, escape="\\")
                    for field in ("name_de","name_fr","name_it","description_de","description_fr","description_it"))))),
                model.item_affair_id.in_(select(Affair.id).where(or_(*(getattr(Affair, field).ilike(term, escape="\\")
                    for field in ("title_de","title_fr","title_it","number"))))),
            ])
        statement = statement.where(or_(*matches))
    if canton:
        statement = statement.where(model.body_id.in_(select(Body.id).where(Body.canton_key == canton.upper())))
    date_column = getattr(model, spec.date_field)
    if year:
        statement = statement.where(extract("year", date_column) == year)
    if month:
        statement = statement.where(extract("month", date_column) == month)
    if date_from:
        statement = statement.where(date_column >= datetime.combine(date_from, time.min))
    if date_to:
        statement = statement.where(date_column < datetime.combine(date_to + timedelta(days=1), time.min))
    if affair_id:
        statement = statement.where(related_entity_condition(dataset, model, [affair_id]))
    if category or subcategory:
        ids = category_ids(db, subcategory or category)
        affair_ids = select(AffairClassification.affair_id).where(AffairClassification.category_id.in_(ids))
        inherited = related_entity_condition(dataset, model, affair_ids)
        own = key.in_(select(EntityClassification.entity_id).where(
                EntityClassification.dataset == dataset, EntityClassification.category_id.in_(ids)))
        statement = statement.where(or_(inherited, own))
    return statement


def list_entities(db, dataset, *, q=None, canton=None, category=None, subcategory=None,
                  year=None, month=None, date_from=None, date_to=None, affair_id=None,
                  group_id=None, person_id=None,
                  agenda_id=None, meeting_id=None,
                  page=1, page_size=10, record_ids=None):
    spec = ENTITIES[dataset]
    model = spec.model
    key = model.pk if dataset == "documents" else model.id
    date_column = getattr(model, spec.date_field)
    statement = entity_statement(db, dataset, q=q, canton=canton, category=category, subcategory=subcategory,
        year=year, month=month, date_from=date_from, date_to=date_to, affair_id=affair_id,
        group_id=group_id, person_id=person_id, agenda_id=agenda_id, meeting_id=meeting_id)
    if record_ids is not None:
        statement = statement.where(key.in_(record_ids))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    key = model.pk if dataset == "documents" else model.id
    rows = db.scalars(statement.order_by(date_column.desc().nullslast(), key.desc()).limit(page_size).offset((page - 1) * page_size)).all()
    body_ids = {row.body_id for row in rows if row.body_id is not None}
    cantons = dict(db.execute(select(Body.id, Body.canton_key).where(Body.id.in_(body_ids))).all()) if body_ids else {}
    items = []
    meetings = {meeting.id: meeting for meeting in db.scalars(select(Meeting).where(Meeting.id.in_(
        {row.meeting_id for row in rows if row.meeting_id is not None}))) } if dataset == "agendas" else {}
    affairs = {affair.id: affair for affair in db.scalars(select(Affair).where(Affair.id.in_(
        {row.item_affair_id for row in rows if row.item_affair_id is not None}))) } if dataset == "agendas" else {}
    for row in rows:
        linked = related_affair_ids(db, dataset, row)
        categories = db.execute(select(ClassificationCategory.code, ClassificationCategory.name_de).join(
            AffairClassification, AffairClassification.category_id == ClassificationCategory.id
        ).where(AffairClassification.affair_id.in_(linked)).distinct()).all() if linked else []
        own = db.execute(select(ClassificationCategory.code, ClassificationCategory.name_de).join(
            EntityClassification, EntityClassification.category_id == ClassificationCategory.id
        ).where(EntityClassification.dataset == dataset, EntityClassification.entity_id == entity_key(dataset, row))).all()
        categories = sorted(set(categories) | set(own))
        if any(code != "other" for code, _ in categories):
            categories = [(code, name) for code, name in categories if code != "other"]
        title = next((getattr(row, field) for field in spec.title_fields if getattr(row, field)), f"{dataset} {entity_key(dataset, row)}")
        presentation = agenda_presentation(row, meetings.get(row.meeting_id), affairs.get(row.item_affair_id)) if dataset == "agendas" else record_presentation(db,dataset,row)
        title = presentation.get("title") or title
        items.append(dict(id=entity_key(dataset, row), source_id=getattr(row, "source_id", entity_key(dataset, row)),
                          title=" ".join(title.split())[:240], date=getattr(row, spec.date_field),
                          canton=cantons.get(row.body_id), affair_ids=sorted(linked),
                          categories=[dict(code=code, name=name) for code, name in categories]))
        items[-1].update(presentation)
    return jsonable_encoder(dict(items=items, pagination=dict(page=page, page_size=page_size, total_items=total, total_pages=ceil(total / page_size))))


def serialize_entity(entity):
    return jsonable_encoder({column.key: getattr(entity, column.key) for column in entity.__table__.columns
                             if column.key != "sync_fingerprint"})


def agenda_presentation(agenda, meeting=None, affair=None):
    """Use actual related content when upstream supplies an untitled agenda item."""
    def title(entity, prefix):
        return next((getattr(entity, prefix + language, None) for language in ("de","fr","it","rm")
                     if getattr(entity, prefix + language, None)), None) if entity is not None else None
    affair_title = title(affair, "title_")
    meeting_title = title(meeting, "name_")
    own = agenda.item_title or agenda.item_description
    return dict(title=" ".join((own or affair_title or meeting_title or agenda.item_affair_number or "").split())[:240] or None,
        title_origin="item" if own else "affair" if affair_title else "meeting" if meeting_title else "missing",
        item_number=agenda.item_number_display or agenda.item_number,
        source_url=agenda.item_url,
        meeting=dict(id=meeting.id,title=meeting_title,date=meeting.begin_date) if meeting else None,
        affair=dict(id=affair.id,title=affair_title,number=affair.number) if affair else None)


def affair_related_data(db, affair_id):
    # Return the first page with totals; the entity list endpoint supports
    # affair_id so large histories remain fully browsable without giant responses.
    return {dataset: list_entities(db, dataset, affair_id=affair_id, page_size=20)
            for dataset in ENTITIES if dataset not in {"affairs", "interests"}}


def record_presentation(db, dataset, entity):
    """Give standalone and supporting records their actual political context."""
    def named(row, prefix):
        return next((getattr(row,prefix+lang,None) for lang in ("de","fr","it","en","rm")
                     if getattr(row,prefix+lang,None)),None) if row is not None else None
    meeting_id=getattr(entity,"meeting_id",None)
    agenda_id=getattr(entity,"agenda_id",None)
    agenda=db.get(Agenda,agenda_id) if agenda_id is not None else None
    if meeting_id is None and agenda is not None:
        meeting_id=agenda.meeting_id
    meeting=db.get(Meeting,meeting_id) if meeting_id is not None else None
    affair_id=getattr(entity,"item_affair_id",None) or getattr(entity,"affair_id",None)
    if affair_id is None and agenda is not None:
        affair_id=agenda.item_affair_id
    affair=db.get(Affair,affair_id) if affair_id is not None else None
    group_id=getattr(entity,"group_id",None) or (meeting.group_id if meeting else None)
    group=db.get(PoliticalGroup,group_id) if group_id is not None else None
    person_id=getattr(entity,"person_id",None)
    person=db.get(Person,person_id) if person_id is not None else None
    body_id=entity.body_id or (affair.body_id if affair else None) or (meeting.body_id if meeting else None)
    body=db.get(Body,body_id) if body_id is not None else None
    affair_title=named(affair,"title_")
    meeting_title=named(meeting,"name_")
    title=next((getattr(entity,field) for field in ENTITIES[dataset].title_fields if getattr(entity,field)),None)
    if dataset == "texts":
        title=named(entity,"type_") or affair_title
    if dataset == "events":
        title=named(entity,"title_") or named(entity,"title_harmonized_")
    if dataset == "votings" and not title:
        title=affair_title or meeting_title
    return dict(title=" ".join(title.split())[:240] if title else None,
        agenda=dict(id=agenda.id,title=agenda.item_title or agenda.item_description or agenda.item_affair_number) if agenda else None,
        context_title=affair_title or meeting_title,
        meeting=dict(id=meeting.id,title=meeting_title,date=meeting.begin_date) if meeting else None,
        affair=dict(id=affair.id,title=affair_title,number=affair.number) if affair else None,
        group=dict(id=group.id,title=named(group,"name_")) if group else None,
        person=dict(id=person.id,fullname=person.fullname,party=person.party_de or person.party_harmonized_de) if person else None,
        body=dict(name=body.name_de or body.name_fr or body.name_it or body.name,canton=body.canton_key) if body else None,
        canton=body.canton_key if body else None,
        source_url=getattr(entity,"url",None) or getattr(entity,"details_url",None),
        decision=getattr(entity,"decision",None),location=getattr(entity,"location",None),
        kind=named(entity,"type_name_") or named(entity,"type_harmonized_") or named(entity,"type_"),
        state=named(entity,"state_name_") or getattr(entity,"state",None),
        role=named(entity,"role_name_") if dataset == "interests" else None)


def affair_changes(db, affair_id, limit=100):
    related = select(ChangeEventAffair.change_event_id).where(ChangeEventAffair.affair_id == affair_id)
    events = db.scalars(select(ChangeEvent).where(ChangeEvent.change_type != "ignored", or_(ChangeEvent.affair_id == affair_id, ChangeEvent.id.in_(related)))
                       .order_by(ChangeEvent.detected_at.desc(), ChangeEvent.id.desc()).limit(limit)).all()
    from app.services.notification_content import change_identity
    entities = {}
    for dataset in {event.dataset for event in events if event.dataset in ENTITIES}:
        model = ENTITIES[dataset].model
        primary = model.pk if dataset == "documents" else model.id
        ids = [event.source_id for event in events if event.dataset == dataset]
        entities[dataset] = {getattr(row, "pk" if dataset == "documents" else "id"): row
                             for row in db.scalars(select(model).where(primary.in_(ids)))}
    result, seen = [], set()
    for event in events:
        entity = entities.get(event.dataset, {}).get(event.source_id)
        identity = change_identity(event, entity)
        if identity in seen:
            continue
        seen.add(identity)
        title = next((getattr(entity, field) for field in ENTITIES[event.dataset].title_fields
                      if entity is not None and getattr(entity, field, None)), None) if event.dataset in ENTITIES else None
        result.append(jsonable_encoder(dict(id=event.id, dataset=event.dataset, source_id=event.source_id,
                      title=title, available=entity is not None, change_type=event.change_type,
                      description=event.description, detected_at=event.detected_at)))
    return result


def search_all_entities(db, datasets=None, *, page=1, page_size=10, **filters):
    from sqlalchemy import literal, union_all
    selected = list(dict.fromkeys(datasets or ENTITIES))
    if any(dataset not in ENTITIES for dataset in selected):
        raise ValueError("Unknown dataset")
    parts = []
    for dataset in selected:
        spec = ENTITIES[dataset]
        key = spec.model.pk if dataset == "documents" else spec.model.id
        statement = entity_statement(db, dataset, direct_search=True, **filters)
        parts.append(statement.with_only_columns(literal(dataset).label("dataset"), key.label("record_id"),
                     getattr(spec.model, spec.date_field).label("date")).order_by(None))
    combined = union_all(*parts).subquery()
    total = db.scalar(select(func.count()).select_from(combined)) or 0
    rows = db.execute(select(combined).order_by(combined.c.date.desc().nullslast(),
        combined.c.dataset, combined.c.record_id.desc()).limit(page_size).offset((page-1)*page_size)).all()
    hydrated = {}
    for dataset in selected:
        ids = [row.record_id for row in rows if row.dataset == dataset]
        if ids:
            result = list_entities(db, dataset, record_ids=ids, page_size=page_size)
            for item in result["items"]:
                item["dataset"] = dataset
                hydrated[(dataset, item["id"])] = item
    return {"items": [hydrated[(row.dataset, row.record_id)] for row in rows],
            "pagination": {"page": page, "page_size": page_size, "total_items": total,
                           "total_pages": ceil(total/page_size)}}
