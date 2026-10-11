"""Normalize upstream values to their persisted representation before comparison."""
from sqlalchemy import String


def normalize_values(model, values):
    return {key: str(value) if value is not None and isinstance(
        model.__table__.columns[key].type, String) else value
        for key, value in values.items()}
