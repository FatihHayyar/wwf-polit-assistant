from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.models.entities import Body
from app.schemas.canton import CantonResponse


CANTON_NAMES = {
    "AG": "Aargau",
    "AI": "Appenzell Innerrhoden",
    "AR": "Appenzell Ausserrhoden",
    "BE": "Bern",
    "BL": "Basel-Landschaft",
    "BS": "Basel-Stadt",
    "FR": "Fribourg",
    "GE": "Genève",
    "GL": "Glarus",
    "GR": "Graubünden",
    "JU": "Jura",
    "LU": "Luzern",
    "NE": "Neuchâtel",
    "NW": "Nidwalden",
    "OW": "Obwalden",
    "SG": "St. Gallen",
    "SH": "Schaffhausen",
    "SO": "Solothurn",
    "SZ": "Schwyz",
    "TG": "Thurgau",
    "TI": "Ticino",
    "UR": "Uri",
    "VD": "Vaud",
    "VS": "Valais",
    "ZG": "Zug",
    "ZH": "Zürich",
}


def get_cantons(
    db: Session,
) -> list[CantonResponse]:
    statement = (
        select(distinct(Body.canton_key))
        .where(
            Body.canton_key.is_not(None),
            Body.canton_key != "",
        )
        .order_by(Body.canton_key)
    )

    canton_codes = db.scalars(statement).all()

    return [
        CantonResponse(
            code=code,
            name=CANTON_NAMES.get(code, code),
        )
        for code in canton_codes
        if code in CANTON_NAMES
    ]