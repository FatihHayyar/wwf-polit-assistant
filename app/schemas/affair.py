from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AffairResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body_id: int | None = None
    body_key: str | None = None
    number: str | None = None
    external_id: str | None = None

    title_de: str | None = None
    title_fr: str | None = None
    title_it: str | None = None

    type_harmonized_de: str | None = None
    state_name_harmonized_de: str | None = None

    begin_date: datetime | None = None
    end_date: datetime | None = None
    active: bool | None = None

    url_external_de: str | None = None
