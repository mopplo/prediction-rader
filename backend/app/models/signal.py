from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        UniqueConstraint("market_id", "signal_type", name="uq_signals_market_type"),
        Index("ix_signals_type_score", "signal_type", "signal_score"),
        Index("ix_signals_market_computed", "market_id", "computed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    change_1h: Mapped[float] = mapped_column(Float, nullable=True)
    change_24h: Mapped[float] = mapped_column(Float, nullable=True)
    change_7d: Mapped[float] = mapped_column(Float, nullable=True)
    volume_spike: Mapped[float] = mapped_column(Float, nullable=True)
    signal_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    signal_reason: Mapped[str] = mapped_column(Text, nullable=True)
    probability_component: Mapped[float] = mapped_column(Float, nullable=True)
    volume_component: Mapped[float] = mapped_column(Float, nullable=True)
    liquidity_component: Mapped[float] = mapped_column(Float, nullable=True)
    persistence_component: Mapped[float] = mapped_column(Float, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    market = relationship("Market", back_populates="signals")
