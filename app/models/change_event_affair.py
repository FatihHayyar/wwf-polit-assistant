from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChangeEventAffair(Base):
    __tablename__ = "change_event_affairs"

    change_event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("change_events.id", ondelete="CASCADE"), primary_key=True,
    )
    affair_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
