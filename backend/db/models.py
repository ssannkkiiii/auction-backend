import enum
from datetime import datetime
from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class LotStatus(str, enum.Enum):
    running = "running"
    ended = "ended"


class Lot(Base):
    __tablename__ = "lots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), default="")
    start_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[LotStatus] = mapped_column(
        Enum(LotStatus), default=LotStatus.running, nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    bids: Mapped[list["Bid"]] = relationship("Bid", back_populates="lot")


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lots.id", ondelete="CASCADE"), nullable=False)
    bidder: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    lot: Mapped["Lot"] = relationship("Lot", back_populates="bids")
