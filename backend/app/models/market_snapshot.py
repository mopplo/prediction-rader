from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    __table_args__ = (
        UniqueConstraint("market_id", "captured_at", name="uq_snapshots_market_captured"),
        Index("ix_market_snapshots_market_captured", "market_id", "captured_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    volume_24h: Mapped[float] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float] = mapped_column(Float, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    market = relationship("Market", back_populates="snapshots")
