from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.canton import CantonResponse
from app.services.canton_service import get_cantons


router = APIRouter(
    prefix="/api/v1/cantons",
    tags=["Cantons"],
)


@router.get("", response_model=list[CantonResponse])
def list_cantons(
    db: Session = Depends(get_db),
) -> list[CantonResponse]:
    return get_cantons(db)