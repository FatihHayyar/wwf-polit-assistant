from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class UserRecordWatch(Base):
    __tablename__ = "user_record_watches"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    dataset: Mapped[str] = mapped_column(String(50), primary_key=True)
    record_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
