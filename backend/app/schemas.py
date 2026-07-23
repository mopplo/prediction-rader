from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SignalComponents(BaseModel):
    probability: float | None = None
    volume: float | None = None
    liquidity: float | None = None
    persistence: float | None = None


class MarketSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str | None = None
    category: str | None = None
    probability: float | None = Field(default=None, serialization_alias="probability")
    volume: float | None = None
    liquidity: float | None = None
    change24h: float | None = None
    change7d: float | None = None
    signal_score: float | None = None
    attention_score: float | None = None
    market_significance: float | None = None
    confidence: float | None = None
    confidence_label: str | None = None
    signal_reason: str | None = None
    volume_spike: float | None = None
    signal_type: str | None = None
    updated_at: datetime | None = None
    polymarket_url: str | None = None


class MarketDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str | None = None
    probability: float | None = None
    change1h: float | None = None
    change24h: float | None = None
    change7d: float | None = None
    change7d_unavailable_reason: str | None = None
    volume: float | None = None
    volume_1wk: float | None = None
    volume_spike: float | None = None
    liquidity: float | None = None
    signal_score: float | None = None
    attention_score: float | None = None
    market_significance: float | None = None
    confidence: float | None = None
    confidence_label: str | None = None
    signal_reason: str | None = None
    why_it_moved: list[str] = Field(default_factory=list)
    signal_components: SignalComponents | None = None
    category: str | None = None
    image_url: str | None = None
    end_date: datetime | None = None
    updated_at: datetime | None = None
    last_synced_at: datetime | None = None
    polymarket_url: str | None = None
    market_status: str | None = None
    resolves_in_days: int | None = None
    history_coverage_hours: float | None = None
    has_24h_history: bool = False
    has_7d_history: bool = False
    history: list[dict[str, Any]] = Field(default_factory=list)


class DailyRadarItem(BaseModel):
    rank: int
    market_id: str
    title: str
    signal_score: float
    confidence: float | None = None
    confidence_label: str | None = None
    signal_reason: str | None = None
    change24h: float | None = None
    volume_spike: float | None = None
    why_it_moved: list[str] = Field(default_factory=list)


class NarrativeTrendItem(BaseModel):
    id: int
    title: str
    category: str | None = None
    market_count: int
    active_count: int
    median_abs_change_24h: float | None = None
    aggregate_volume_spike: float | None = None
    direction_coherence: float | None = None
    dominant_direction: str | None = None
    narrative_score: float
    representative_market_id: str | None = None
    summary: str | None = None


class PaginatedMarkets(BaseModel):
    items: list[MarketSummary]
    total: int
    limit: int
    offset: int


class RadarStats(BaseModel):
    markets_tracked: int
    active_signals: int
    last_synced_at: datetime | None = None
    sync_interval_minutes: int = 120
