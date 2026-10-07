from pydantic import BaseModel


class AffairTypeResponse(BaseModel):
    value: str
    label: str