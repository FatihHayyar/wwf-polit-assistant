from pydantic import BaseModel


class SubcategoryResponse(BaseModel):
    id: int
    code: str
    name_de: str | None = None
    name_fr: str | None = None
    name_it: str | None = None


class CategoryResponse(BaseModel):
    id: int
    code: str
    name_de: str | None = None
    name_fr: str | None = None
    name_it: str | None = None

    subcategories: list[SubcategoryResponse]