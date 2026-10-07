from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.affair_type import AffairTypeResponse
from app.services.affair_type_service import get_affair_types


router = APIRouter(
    prefix="/api/v1/affair-types",
    tags=["Affair Types"],
)


@router.get("", response_model=list[AffairTypeResponse])
def list_affair_types(
    db: Session = Depends(get_db),
) -> list[AffairTypeResponse]:
    return get_affair_types(db)