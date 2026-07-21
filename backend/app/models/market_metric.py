from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class MarketMetric(Base):
    __tablename__ = "market_metrics"
    __table_args__ = (
        Index("ix_market_metrics_signal_score", "signal_score"),
        Index("ix_market_metrics_computed_at", "computed_at"),
    )

    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"), primary_key=True)
    change_1h: Mapped[float] = mapped_column(Float, nullable=True)
    change_24h: Mapped[float] = mapped_column(Float, nullable=True)
    change_7d: Mapped[float] = mapped_column(Float, nullable=True)
    volume_spike: Mapped[float] = mapped_column(Float, nullable=True)
    signal_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attention_score: Mapped[float] = mapped_column(Float, nullable=True)
    market_significance: Mapped[float] = mapped_column(Float, nullable=True)
    data_confidence: Mapped[float] = mapped_column(Float, nullable=True)
    signal_reason: Mapped[str] = mapped_column(Text, nullable=True)
    why_it_moved: Mapped[str] = mapped_column(Text, nullable=True)
    probability_component: Mapped[float] = mapped_column(Float, nullable=True)
    volume_component: Mapped[float] = mapped_column(Float, nullable=True)
    liquidity_component: Mapped[float] = mapped_column(Float, nullable=True)
    persistence_component: Mapped[float] = mapped_column(Float, nullable=True)
    has_24h_history: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_7d_history: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    history_coverage_hours: Mapped[float] = mapped_column(Float, nullable=True)
    eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    market = relationship("Market", back_populates="metrics")
