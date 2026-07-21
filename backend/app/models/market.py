from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Market(Base):
    __tablename__ = "markets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    yes_token_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    current_probability: Mapped[float] = mapped_column(Float, nullable=True)
    volume_24h: Mapped[float] = mapped_column(Float, nullable=True)
    volume_1wk: Mapped[float] = mapped_column(Float, nullable=True)
    liquidity: Mapped[float] = mapped_column(Float, nullable=True)
    category: Mapped[str] = mapped_column(String(128), nullable=True)
    condition_id: Mapped[str] = mapped_column(String(128), nullable=True)
    group_item_id: Mapped[str] = mapped_column(String(128), nullable=True, index=True)
    topic_key: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    event_slug: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    event_title: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[str] = mapped_column(Text, nullable=True)
    market_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    eligibility_status: Mapped[str] = mapped_column(String(32), nullable=True, index=True)
    eligibility_reason: Mapped[str] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    snapshots = relationship("MarketSnapshot", back_populates="market", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="market", cascade="all, delete-orphan")
    metrics = relationship("MarketMetric", back_populates="market", uselist=False, cascade="all, delete-orphan")
