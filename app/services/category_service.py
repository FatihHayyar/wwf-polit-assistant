from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.classification import ClassificationCategory
from app.schemas.category import CategoryResponse, SubcategoryResponse


def get_categories(
    db: Session,
) -> list[CategoryResponse]:
    statement = (
        select(ClassificationCategory)
        .where(
            ClassificationCategory.active.is_(True),
            ClassificationCategory.is_fallback.is_(False),
        )
        .order_by(
            ClassificationCategory.sort_order,
            ClassificationCategory.id,
        )
    )

    categories = list(db.scalars(statement).all())

    parent_categories = [
        category
        for category in categories
        if category.parent_id is None
    ]

    result: list[CategoryResponse] = []

    for parent in parent_categories:
        subcategories = [
            SubcategoryResponse(
                id=category.id,
                code=category.code,
                name_de=category.name_de,
                name_fr=category.name_fr,
                name_it=category.name_it,
            )
            for category in categories
            if category.parent_id == parent.id
        ]

        result.append(
            CategoryResponse(
                id=parent.id,
                code=parent.code,
                name_de=parent.name_de,
                name_fr=parent.name_fr,
                name_it=parent.name_it,
                subcategories=subcategories,
            )
        )

    return result