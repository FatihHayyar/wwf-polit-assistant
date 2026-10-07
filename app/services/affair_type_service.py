from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.models.entities import Affair
from app.schemas.affair_type import AffairTypeResponse


def get_affair_types(
    db: Session,
) -> list[AffairTypeResponse]:
    statement = (
        select(distinct(Affair.type_harmonized_de))
        .where(
            Affair.type_harmonized_de.is_not(None),
            Affair.type_harmonized_de != "",
        )
        .order_by(Affair.type_harmonized_de)
    )

    affair_types = db.scalars(statement).all()

    return [
        AffairTypeResponse(
            value=affair_type,
            label=affair_type,
        )
        for affair_type in affair_types
    ]