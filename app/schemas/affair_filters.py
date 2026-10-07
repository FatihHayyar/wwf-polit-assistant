from pydantic import BaseModel, Field


class AffairFilters(BaseModel):
    q: str | None = None
    canton: str | None = None

    category: str | None = None
    subcategory: str | None = None

    year: int | None = Field(default=None, ge=1900, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)

    affair_type: str | None = None
    state: str | None = None

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=10)

    sort: str = "newest"

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
