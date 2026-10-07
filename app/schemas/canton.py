from pydantic import BaseModel


class CantonResponse(BaseModel):
    code: str
    name: str