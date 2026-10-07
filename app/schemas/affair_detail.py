from datetime import datetime

from pydantic import BaseModel


class AffairDetailClassificationResponse(BaseModel):
    category_code: str
    category_name_de: str | None = None
    parent_category_code: str | None = None
    parent_category_name_de: str | None = None
    confidence: str | None = None
    score: float | None = None


class AffairDetailTextResponse(BaseModel):
    id: int
    text_de: str | None = None
    text_fr: str | None = None
    text_it: str | None = None
    type_de: str | None = None
    date: datetime | None = None


class AffairDetailResponse(BaseModel):
    # Basic affair information
    id: int
    number: str | None = None

    title_de: str | None = None
    title_fr: str | None = None
    title_it: str | None = None

    title_long_de: str | None = None
    title_long_fr: str | None = None
    title_long_it: str | None = None

    affair_type: str | None = None
    state: str | None = None

    begin_date: datetime | None = None
    end_date: datetime | None = None
    active: bool | None = None

    # Parliament / body information
    body_id: int | None = None
    body_key: str | None = None
    body_name_de: str | None = None
    canton: str | None = None

    # WWF classification
    classifications: list[AffairDetailClassificationResponse]

    # Parliamentary texts
    texts: list[AffairDetailTextResponse]

    # Official source
    original_url: str | None = None