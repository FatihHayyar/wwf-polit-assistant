from sqlalchemy import BigInteger, ForeignKey, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class EntityClassification(Base):
    __tablename__ = "entity_classifications"
    dataset: Mapped[str] = mapped_column(String(50), primary_key=True)
    entity_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    category_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("classification_categories.id", ondelete="RESTRICT"), primary_key=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    classifier_version: Mapped[str] = mapped_column(String(50), nullable=False)
