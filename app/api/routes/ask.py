"""Dialogue-oriented query: a question in natural language becomes a search."""
from __future__ import annotations

import time
from datetime import date

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.rate_limit import ASK_PER_IP, client_address, enforce
from app.db.database import get_db
from app.services.affair_type_service import get_affair_types
from app.services.entity_service import list_entities
from app.services.query_interpreter import get_interpreter


router = APIRouter(prefix="/api/v1/ask", tags=["Dialog"])

_affair_types_cache: tuple[float, list[str]] = (0.0, [])


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=300)
    page: int = Field(default=1, ge=1)


def known_affair_types(db: Session) -> list[str]:
    """Distinct affair types change rarely; refresh at most every ten minutes."""
    global _affair_types_cache
    loaded_at, values = _affair_types_cache
    if not values or time.monotonic() - loaded_at > 600:
        values = [item.value for item in get_affair_types(db)]
        _affair_types_cache = (time.monotonic(), values)
    return values


@router.post("")
def ask(payload: Question, request: Request, db: Session = Depends(get_db)):
    enforce((f"ask-ip:{client_address(request)}", ASK_PER_IP))
    interpretation = get_interpreter().interpret(db, payload.question, known_affair_types(db), date.today())
    results = list_entities(db, interpretation.dataset, page=payload.page, page_size=10, **interpretation.filters())
    return {
        "question": payload.question,
        "dataset": interpretation.dataset,
        "filters": interpretation.filters(),
        "recognised": [vars(item) for item in interpretation.recognised],
        "results": results,
    }
