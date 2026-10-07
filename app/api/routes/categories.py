from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.category import CategoryResponse
from app.services.category_service import get_categories


router = APIRouter(
    prefix="/api/v1/categories",
    tags=["Categories"],
)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
):
    return get_categories(db)