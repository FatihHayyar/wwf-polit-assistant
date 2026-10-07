from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.affair_detail import AffairDetailResponse
from app.schemas.affair_filters import AffairFilters
from app.schemas.pagination import AffairListResponse
from app.services.affair_service import (
    get_affair_detail,
    get_affairs,
)


router = APIRouter(
    prefix="/api/v1/affairs",
    tags=["Affairs"],
)


@router.get("", response_model=AffairListResponse)
def list_affairs(
    q: str | None = Query(default=None),
    canton: str | None = Query(
        default=None,
        min_length=2,
        max_length=2,
    ),
    category: str | None = Query(default=None),
    subcategory: str | None = Query(default=None),
    year: int | None = Query(
        default=None,
        ge=1900,
        le=2100,
    ),
    month: int | None = Query(
        default=None,
        ge=1,
        le=12,
    ),
    affair_type: str | None = Query(default=None),
    state: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
) -> AffairListResponse:
    filters = AffairFilters(
        q=q,
        canton=canton,
        category=category,
        subcategory=subcategory,
        year=year,
        month=month,
        affair_type=affair_type,
        state=state,
        page=page,
        page_size=10,
    )

    return get_affairs(
        db=db,
        filters=filters,
    )


@router.get(
    "/{affair_id}",
    response_model=AffairDetailResponse,
)
def get_affair(
    affair_id: int,
    db: Session = Depends(get_db),
) -> AffairDetailResponse:
    affair = get_affair_detail(
        db=db,
        affair_id=affair_id,
    )

    if affair is None:
        raise HTTPException(
            status_code=404,
            detail="Affair not found",
        )

    return affair