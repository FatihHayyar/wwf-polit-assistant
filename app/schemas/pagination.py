from pydantic import BaseModel

from app.schemas.affair import AffairResponse


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class AffairListResponse(BaseModel):
    items: list[AffairResponse]
    pagination: PaginationMeta