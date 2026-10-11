from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.entity_registry import ENTITIES, PRIMARY_DATASETS
from app.services.entity_relations import related_affair_ids
from app.services.entity_service import affair_changes, affair_related_data, list_entities, serialize_entity, agenda_presentation, record_presentation

Dataset = Literal["affairs", "agendas", "meetings", "votings", "events", "documents", "texts", "groups", "interests"]
router = APIRouter(prefix="/api/v1/entities", tags=["Entities"])


@router.get("")
def available_entities():
    return {"datasets": list(ENTITIES), "navigation": list(ENTITIES),
            "supporting_datasets": [key for key in ENTITIES if key not in PRIMARY_DATASETS],
            "classification_basis": "own_content_and_related_affairs"}


@router.get("/search")
def unified_search(datasets: list[Dataset] | None = Query(None), q: str | None = None,
                   canton: str | None = None, category: str | None = None, subcategory: str | None = None,
                   date_from: date | None = None, date_to: date | None = None,
                   page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
                   db: Session = Depends(get_db)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must not be after date_to")
    from app.services.entity_service import search_all_entities
    return search_all_entities(db, datasets, q=q, canton=canton, category=category,
                              subcategory=subcategory, date_from=date_from, date_to=date_to,
                              page=page, page_size=page_size)


@router.get("/{dataset}")
def search_entities(dataset: Dataset, q: str | None = None, canton: str | None = None,
                    category: str | None = None, subcategory: str | None = None,
                    year: int | None = Query(None, ge=1900, le=2100),
                    month: int | None = Query(None, ge=1, le=12),
                    date_from: date | None = None, date_to: date | None = None,
                    affair_id: int | None = Query(None, gt=0),
                    group_id: int | None = Query(None, gt=0), person_id: int | None = Query(None, gt=0),
                    agenda_id: int | None = Query(None, gt=0), meeting_id: int | None = Query(None, gt=0),
                    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
                    db: Session = Depends(get_db)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must not be after date_to")
    if (group_id is not None and dataset != "meetings") or (person_id is not None and dataset != "interests"):
        raise HTTPException(422, "group_id applies to meetings; person_id applies to interests.")
    if (agenda_id is not None and dataset != "documents") or (meeting_id is not None and dataset not in {"agendas","events","votings","documents"}):
        raise HTTPException(422, "Invalid relationship filter for this dataset.")
    return list_entities(db, dataset, q=q, canton=canton, category=category, subcategory=subcategory,
                         year=year, month=month, date_from=date_from, date_to=date_to,
                         affair_id=affair_id, group_id=group_id, person_id=person_id, agenda_id=agenda_id, meeting_id=meeting_id, page=page, page_size=page_size)


@router.get("/{dataset}/{record_id}")
def entity_detail(dataset: Dataset, record_id: int, db: Session = Depends(get_db)):
    entity = db.get(ENTITIES[dataset].model, record_id)
    if entity is None:
        raise HTTPException(404, "Record not found")
    result = {"dataset": dataset, "record": serialize_entity(entity),
              "affair_ids": sorted(related_affair_ids(db, dataset, entity))}
    result.update(record_presentation(db,dataset,entity))
    from app.models.entities import Affair
    result["linked_affairs"] = [dict(id=affair.id, title=affair.title_de or affair.title_fr or affair.title_it,
                                     number=affair.number)
                                for linked_id in result["affair_ids"]
                                if (affair := db.get(Affair, linked_id)) is not None]
    if dataset == "affairs":
        from app.services.affair_service import get_affair_detail
        result["detail"] = get_affair_detail(db, record_id)
    if dataset == "agendas":
        from app.models.entities import Meeting, Affair, PoliticalGroup, Body
        meeting = db.get(Meeting, entity.meeting_id) if entity.meeting_id is not None else None
        affair = db.get(Affair, entity.item_affair_id) if entity.item_affair_id is not None else None
        result.update(agenda_presentation(entity, meeting, affair))
        body = db.get(Body, entity.body_id) if entity.body_id is not None else None
        result["body"] = dict(name=body.name_de or body.name_fr or body.name_it or body.name, canton=body.canton_key) if body else None
        if meeting:
            result["meeting_record"] = serialize_entity(meeting)
            group = db.get(PoliticalGroup, meeting.group_id) if meeting.group_id is not None else None
            result["group"] = dict(id=group.id,title=group.name_de or group.name_fr or group.name_it) if group else None
        result["documents"] = list_entities(db, "documents", agenda_id=record_id, page_size=20)
    if dataset == "meetings":
        result["agendas"] = list_entities(db, "agendas", meeting_id=record_id, page_size=20)
        result["related"] = {key:list_entities(db,key,meeting_id=record_id,page_size=20) for key in ("votings","events","documents")}
    if dataset == "groups":
        result["meetings"] = list_entities(db, "meetings", group_id=record_id, page_size=20)
    if dataset == "interests" and entity.person_id is not None:
        from app.models.entities import Person
        person = db.get(Person, entity.person_id)
        result["person"] = {"id": person.id, "fullname": person.fullname,
                            "party": person.party_de or person.party_harmonized_de} if person else None
    return result
