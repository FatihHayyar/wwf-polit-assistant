import math

from sqlalchemy import Select, extract, func, or_, select
from sqlalchemy.orm import Session

from app.models.classification import (
    AffairClassification,
    ClassificationCategory,
)
from app.models.entities import (
    Affair,
    Body,
    ParliamentaryText,
)
from app.schemas.affair_detail import (
    AffairDetailClassificationResponse,
    AffairDetailResponse,
    AffairDetailTextResponse,
)
from app.schemas.affair_filters import AffairFilters
from app.schemas.pagination import AffairListResponse, PaginationMeta


def _apply_filters(
    statement: Select,
    filters: AffairFilters,
) -> Select:
    # Canton filter
    #
    # Affair.body_key is not always a canton code.
    # Therefore canton filtering is done through bodies.canton_key.
    if filters.canton:
        statement = (
            statement
            .join(
                Body,
                Body.id == Affair.body_id,
            )
            .where(
                Body.canton_key == filters.canton.upper()
            )
        )

    # Keyword search
    #
    # MVP:
    # Search only in affair titles, long titles and affair number.
    #
    # Full-text search inside parliamentary texts and documents
    # will be added later with proper database indexing.
    if filters.q:
        search_value = filters.q.strip()

        if search_value:
            search_term = f"%{search_value}%"

            statement = statement.where(
                or_(
                    Affair.title_de.ilike(search_term),
                    Affair.title_fr.ilike(search_term),
                    Affair.title_it.ilike(search_term),
                    Affair.title_long_de.ilike(search_term),
                    Affair.title_long_fr.ilike(search_term),
                    Affair.title_long_it.ilike(search_term),
                    Affair.number.ilike(search_term),
                )
            )

    # Year filter
    if filters.year:
        statement = statement.where(
            extract("year", Affair.begin_date) == filters.year
        )

    # Month filter
    if filters.month:
        statement = statement.where(
            extract("month", Affair.begin_date) == filters.month
        )

    # Affair type filter
    #
    # Case-insensitive:
    # motion / Motion / MOTION all match "Motion".
    if filters.affair_type:
        statement = statement.where(
            Affair.type_harmonized_de.ilike(
                filters.affair_type.strip()
            )
        )

    # WWF classification filter
    #
    # Subcategory selected:
    # -> only the selected subcategory
    #
    # Only main category selected:
    # -> main category + all direct subcategories
    if filters.subcategory:
        statement = (
            statement
            .join(
                AffairClassification,
                AffairClassification.affair_id == Affair.id,
            )
            .join(
                ClassificationCategory,
                ClassificationCategory.id
                == AffairClassification.category_id,
            )
            .where(
                ClassificationCategory.code == filters.subcategory
            )
        )

    elif filters.category:
        parent_category_id = (
            select(ClassificationCategory.id)
            .where(
                ClassificationCategory.code == filters.category
            )
            .scalar_subquery()
        )

        statement = (
            statement
            .join(
                AffairClassification,
                AffairClassification.affair_id == Affair.id,
            )
            .join(
                ClassificationCategory,
                ClassificationCategory.id
                == AffairClassification.category_id,
            )
            .where(
                or_(
                    ClassificationCategory.code == filters.category,
                    ClassificationCategory.parent_id
                    == parent_category_id,
                )
            )
        )

    return statement


def get_affairs(
    db: Session,
    filters: AffairFilters,
) -> AffairListResponse:
    # Current page query
    statement = _apply_filters(
        select(Affair),
        filters,
    )

    statement = (
        statement
        .order_by(
            Affair.begin_date.desc().nullslast(),
            Affair.id.desc(),
        )
        .limit(filters.page_size)
        .offset(filters.offset)
    )

    affairs = list(
        db.scalars(statement)
        .unique()
        .all()
    )

    # Count query using exactly the same filters
    count_statement = _apply_filters(
        select(func.count(func.distinct(Affair.id))),
        filters,
    )

    total_items = db.scalar(count_statement) or 0

    total_pages = (
        math.ceil(total_items / filters.page_size)
        if total_items > 0
        else 0
    )

    return AffairListResponse(
        items=affairs,
        pagination=PaginationMeta(
            page=filters.page,
            page_size=filters.page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


def get_affair_detail(
    db: Session,
    affair_id: int,
) -> AffairDetailResponse | None:
    # Load affair and parliamentary body.
    affair_row = db.execute(
        select(Affair, Body)
        .outerjoin(
            Body,
            Body.id == Affair.body_id,
        )
        .where(
            Affair.id == affair_id
        )
    ).first()

    if affair_row is None:
        return None

    affair, body = affair_row

    # Load WWF classifications.
    #
    # category_alias:
    # The category directly assigned to the affair.
    #
    # parent_alias:
    # The optional WWF parent category.
    category_alias = ClassificationCategory.__table__.alias(
        "category"
    )

    parent_alias = ClassificationCategory.__table__.alias(
        "parent_category"
    )

    classification_statement = (
        select(
            category_alias.c.code.label("category_code"),
            category_alias.c.name_de.label("category_name_de"),
            parent_alias.c.code.label("parent_category_code"),
            parent_alias.c.name_de.label("parent_category_name_de"),
            AffairClassification.confidence,
            AffairClassification.score,
        )
        .join(
            category_alias,
            category_alias.c.id
            == AffairClassification.category_id,
        )
        .outerjoin(
            parent_alias,
            parent_alias.c.id
            == category_alias.c.parent_id,
        )
        .where(
            AffairClassification.affair_id == affair_id
        )
        .order_by(
            AffairClassification.score.desc().nullslast()
        )
    )

    classification_rows = db.execute(
        classification_statement
    ).all()

    classifications = [
        AffairDetailClassificationResponse(
            category_code=row.category_code,
            category_name_de=row.category_name_de,
            parent_category_code=row.parent_category_code,
            parent_category_name_de=row.parent_category_name_de,
            confidence=row.confidence,
            score=row.score,
        )
        for row in classification_rows
    ]

    # Load parliamentary texts belonging only to this affair.
    #
    # Important:
    # The database model uses "text_date", not "date".
    text_statement = (
        select(ParliamentaryText)
        .where(
            ParliamentaryText.affair_id == affair_id
        )
        .order_by(
            ParliamentaryText.text_date.asc().nullslast(),
            ParliamentaryText.id.asc(),
        )
    )

    parliamentary_texts = list(
        db.scalars(text_statement).all()
    )

    texts = [
        AffairDetailTextResponse(
            id=text.id,
            text_de=text.text_de,
            text_fr=text.text_fr,
            text_it=text.text_it,
            type_de=text.type_de,
            date=text.text_date,
        )
        for text in parliamentary_texts
    ]

    return AffairDetailResponse(
        id=affair.id,
        number=affair.number,

        title_de=affair.title_de,
        title_fr=affair.title_fr,
        title_it=affair.title_it,

        title_long_de=affair.title_long_de,
        title_long_fr=affair.title_long_fr,
        title_long_it=affair.title_long_it,

        affair_type=affair.type_harmonized_de,
        state=affair.state_name_harmonized_de,

        begin_date=affair.begin_date,
        end_date=affair.end_date,
        active=affair.active,

        body_id=affair.body_id,
        body_key=affair.body_key,
        body_name_de=body.name_de if body else None,
        canton=body.canton_key if body else None,

        classifications=classifications,
        texts=texts,

        original_url=affair.url_external_de,
    )