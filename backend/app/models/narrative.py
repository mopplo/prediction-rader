from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Narrative(Base):
    __tablename__ = "narratives"
    __table_args__ = (
        Index("ix_narratives_topic_key", "topic_key"),
        Index("ix_narratives_computed_at", "computed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic_key: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=True)
    market_count: Mapped[int] = mapped_column(Integer, nullable=False)
    active_count: Mapped[int] = mapped_column(Integer, nullable=False)
    median_abs_change_24h: Mapped[float] = mapped_column(Float, nullable=True)
    aggregate_volume_spike: Mapped[float] = mapped_column(Float, nullable=True)
    direction_coherence: Mapped[float] = mapped_column(Float, nullable=True)
    dominant_direction: Mapped[str] = mapped_column(String(16), nullable=True)
    narrative_score: Mapped[float] = mapped_column(Float, nullable=False)
    representative_market_id: Mapped[str] = mapped_column(
        ForeignKey("markets.id", ondelete="SET NULL"), nullable=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    members = relationship("NarrativeMember", back_populates="narrative", cascade="all, delete-orphan")
    representative_market = relationship("Market", foreign_keys=[representative_market_id])


class NarrativeMember(Base):
    __tablename__ = "narrative_members"
    __table_args__ = (UniqueConstraint("narrative_id", "market_id", name="uq_narrative_member"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    narrative_id: Mapped[int] = mapped_column(ForeignKey("narratives.id", ondelete="CASCADE"), nullable=False)
    market_id: Mapped[str] = mapped_column(ForeignKey("markets.id", ondelete="CASCADE"), nullable=False)

    narrative = relationship("Narrative", back_populates="members")
    market = relationship("Market")
