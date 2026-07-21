from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import Market, MarketMetric, MarketSnapshot, Narrative, Signal
from app.services.polymarket import PricePoint, compute_probability_changes
from app.services.signals import confidence_label
from app.schemas import (
    DailyRadarItem,
    MarketDetail,
    MarketSummary,
    NarrativeTrendItem,
    PaginatedMarkets,
    SignalComponents,
)

router = APIRouter(prefix="/api")


def _build_polymarket_url(market: Market) -> str | None:
    slug = market.event_slug or market.slug
    if not slug:
        return None
    return f"https://polymarket.com/event/{slug}"


def _market_status(market: Market, *, now: datetime) -> tuple[str | None, int | None]:
    if market.is_closed is True:
        return "closed", None
    if market.end_date is not None:
        end_date = _ensure_utc(market.end_date)
        if end_date <= now:
            return "closed", 0
        days = max(1, math.ceil((end_date - now).total_seconds() / 86400))
        return "open", days
    if market.is_active is True:
        return "open", None
    return None, None


def _latest_batch_computed_at(db: Session, signal_type: str) -> datetime | None:
    return db.scalar(
        select(func.max(Signal.computed_at)).where(Signal.signal_type == signal_type)
    )


def _latest_batch_signals(db: Session, signal_type: str) -> list[Signal]:
    latest_computed_at = _latest_batch_computed_at(db, signal_type)
    if latest_computed_at is None:
        return []

    return db.scalars(
        select(Signal).where(
            Signal.signal_type == signal_type,
            Signal.computed_at == latest_computed_at,
        )
    ).all()


def _dedupe_signals_by_market(signals: list[Signal]) -> list[Signal]:
    deduped: dict[str, Signal] = {}
    for signal in signals:
        deduped.setdefault(signal.market_id, signal)
    return list(deduped.values())


def _latest_signal_map(db: Session, signal_type: str | None = None) -> dict[str, Signal]:
    if signal_type:
        signals = _dedupe_signals_by_market(_latest_batch_signals(db, signal_type))
    else:
        latest_by_type: dict[str, Signal] = {}
        for batch_type in ("top_mover", "emerging", "daily_radar"):
            for signal in _dedupe_signals_by_market(_latest_batch_signals(db, batch_type)):
                existing = latest_by_type.get(signal.market_id)
                if existing is None or signal.computed_at > existing.computed_at:
                    latest_by_type[signal.market_id] = signal
        return latest_by_type

    latest: dict[str, Signal] = {}
    for signal in signals:
        latest.setdefault(signal.market_id, signal)
    return latest


def _metric_map(db: Session, market_ids: list[str]) -> dict[str, MarketMetric]:
    if not market_ids:
        return {}
    metrics = db.scalars(select(MarketMetric).where(MarketMetric.market_id.in_(market_ids))).all()
    return {metric.market_id: metric for metric in metrics}


def _parse_why_it_moved(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        return [raw]
    return []


def _to_summary(
    market: Market,
    signal: Signal | None = None,
    metric: MarketMetric | None = None,
) -> MarketSummary:
    return MarketSummary(
        id=market.id,
        title=market.title,
        slug=market.slug,
        category=market.category,
        probability=market.current_probability,
        volume=market.volume_24h,
        liquidity=market.liquidity,
        change24h=(signal.change_24h if signal else metric.change_24h if metric else None),
        change7d=(signal.change_7d if signal else metric.change_7d if metric else None),
        signal_score=(signal.signal_score if signal else metric.signal_score if metric else None),
        attention_score=metric.attention_score if metric else None,
        market_significance=metric.market_significance if metric else None,
        confidence=(signal.confidence if signal else metric.data_confidence if metric else None),
        confidence_label=confidence_label(
            signal.confidence if signal else metric.data_confidence if metric else None
        ),
        signal_reason=(signal.signal_reason if signal else metric.signal_reason if metric else None),
        volume_spike=(signal.volume_spike if signal else metric.volume_spike if metric else None),
        signal_type=signal.signal_type if signal else None,
        updated_at=market.updated_at,
        polymarket_url=_build_polymarket_url(market),
    )


def _change7d_unavailable_reason(market: Market, change_7d: float | None) -> str | None:
    if change_7d is not None:
        return None

    now = datetime.now(tz=UTC)
    if market.market_created_at:
        age = now - market.market_created_at
        age_days = max(0, int(age.total_seconds() // 86400))
        if age_days < 7:
            return f"Only {age_days}d of listing history"

    return "Insufficient 7d price history"


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _history_coverage_hours(snapshots: list[MarketSnapshot], *, now: datetime | None = None) -> float:
    if not snapshots:
        return 0.0
    now = _ensure_utc(now or datetime.now(tz=UTC))
    earliest = min(_ensure_utc(snapshot.captured_at) for snapshot in snapshots)
    return max(0.0, (now - earliest).total_seconds() / 3600)


@router.get("/markets", response_model=PaginatedMarkets)
def list_markets(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedMarkets:
    total = db.scalar(select(func.count()).select_from(Market)) or 0
    markets = db.scalars(
        select(Market).order_by(Market.volume_24h.desc().nullslast()).offset(offset).limit(limit)
    ).all()
    signal_map = _latest_signal_map(db)
    metric_map = _metric_map(db, [market.id for market in markets])
    return PaginatedMarkets(
        items=[
            _to_summary(market, signal_map.get(market.id), metric_map.get(market.id))
            for market in markets
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/top-movers", response_model=list[MarketSummary])
def top_movers(db: Session = Depends(get_db)) -> list[MarketSummary]:
    settings = get_settings()
    signals = sorted(
        _dedupe_signals_by_market(_latest_batch_signals(db, "top_mover")),
        key=lambda signal: (abs(signal.change_24h or 0), signal.signal_score),
        reverse=True,
    )[: settings.top_movers_limit]
    if not signals:
        return []

    market_ids = [signal.market_id for signal in signals]
    markets = db.scalars(select(Market).where(Market.id.in_(market_ids))).all()
    market_map = {market.id: market for market in markets}
    metric_map = _metric_map(db, market_ids)
    return [
        _to_summary(market_map[signal.market_id], signal, metric_map.get(signal.market_id))
        for signal in signals
        if signal.market_id in market_map
    ]


@router.get("/emerging-signals", response_model=list[MarketSummary])
def emerging_signals(db: Session = Depends(get_db)) -> list[MarketSummary]:
    settings = get_settings()
    batch_signals = _dedupe_signals_by_market(_latest_batch_signals(db, "emerging"))
    metric_map = _metric_map(db, [signal.market_id for signal in batch_signals])
    signals = sorted(
        batch_signals,
        key=lambda signal: (
            metric_map[signal.market_id].attention_score
            if signal.market_id in metric_map and metric_map[signal.market_id].attention_score is not None
            else 0,
            signal.volume_spike or 0,
        ),
        reverse=True,
    )[: settings.emerging_signals_limit]
    if not signals:
        return []

    market_ids = [signal.market_id for signal in signals]
    markets = db.scalars(select(Market).where(Market.id.in_(market_ids))).all()
    market_map = {market.id: market for market in markets}
    metric_map = _metric_map(db, market_ids)
    return [
        _to_summary(market_map[signal.market_id], signal, metric_map.get(signal.market_id))
        for signal in signals
        if signal.market_id in market_map
    ]


@router.get("/daily-radar", response_model=list[DailyRadarItem])
def daily_radar(db: Session = Depends(get_db)) -> list[DailyRadarItem]:
    settings = get_settings()
    signals = sorted(
        _dedupe_signals_by_market(_latest_batch_signals(db, "daily_radar")),
        key=lambda signal: (signal.signal_score, signal.confidence or 0),
        reverse=True,
    )[: settings.daily_radar_limit]
    if not signals:
        return []

    market_ids = [signal.market_id for signal in signals]
    markets = db.scalars(select(Market).where(Market.id.in_(market_ids))).all()
    market_map = {market.id: market for market in markets}
    metric_map = _metric_map(db, market_ids)

    items: list[DailyRadarItem] = []
    for index, signal in enumerate(signals, start=1):
        market = market_map.get(signal.market_id)
        if not market:
            continue
        metric = metric_map.get(signal.market_id)
        items.append(
            DailyRadarItem(
                rank=index,
                market_id=market.id,
                title=market.title,
                signal_score=signal.signal_score,
                confidence=signal.confidence,
                confidence_label=confidence_label(signal.confidence),
                signal_reason=signal.signal_reason,
                change24h=signal.change_24h,
                volume_spike=signal.volume_spike,
                why_it_moved=_parse_why_it_moved(metric.why_it_moved if metric else None),
            )
        )
    return items


@router.get("/narrative-trends", response_model=list[NarrativeTrendItem])
def narrative_trends(db: Session = Depends(get_db)) -> list[NarrativeTrendItem]:
    settings = get_settings()
    latest_computed_at = db.scalar(select(func.max(Narrative.computed_at)))
    if latest_computed_at is None:
        return []

    narratives = db.scalars(
        select(Narrative)
        .where(Narrative.computed_at == latest_computed_at)
        .order_by(Narrative.narrative_score.desc(), Narrative.active_count.desc())
        .limit(settings.narrative_trends_limit)
    ).all()

    return [
        NarrativeTrendItem(
            id=narrative.id,
            title=narrative.title,
            category=narrative.category,
            market_count=narrative.market_count,
            active_count=narrative.active_count,
            median_abs_change_24h=narrative.median_abs_change_24h,
            aggregate_volume_spike=narrative.aggregate_volume_spike,
            direction_coherence=narrative.direction_coherence,
            dominant_direction=narrative.dominant_direction,
            narrative_score=narrative.narrative_score,
            representative_market_id=narrative.representative_market_id,
            summary=narrative.summary,
        )
        for narrative in narratives
    ]


@router.get("/market/{market_id}", response_model=MarketDetail)
def market_detail(market_id: str, db: Session = Depends(get_db)) -> MarketDetail:
    market = db.get(Market, market_id)
    if market is None:
        raise HTTPException(status_code=404, detail="Market not found")

    metric = db.get(MarketMetric, market_id)
    signal = db.scalar(
        select(Signal).where(Signal.market_id == market_id).order_by(Signal.computed_at.desc()).limit(1)
    )

    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(days=7)
    snapshots = db.scalars(
        select(MarketSnapshot)
        .where(MarketSnapshot.market_id == market_id, MarketSnapshot.captured_at >= cutoff)
        .order_by(MarketSnapshot.captured_at.desc())
        .limit(672)
    ).all()
    snapshots = list(reversed(snapshots))

    coverage_hours = _history_coverage_hours(snapshots, now=now)
    history = [
        {
            "timestamp": snapshot.captured_at.isoformat(),
            "probability": snapshot.probability,
            "volume24h": snapshot.volume_24h,
        }
        for snapshot in snapshots
    ]

    change_1h = metric.change_1h if metric else (signal.change_1h if signal else None)
    change_24h = metric.change_24h if metric else (signal.change_24h if signal else None)
    change_7d = metric.change_7d if metric else (signal.change_7d if signal else None)
    volume_spike = metric.volume_spike if metric else (signal.volume_spike if signal else None)
    signal_score = metric.signal_score if metric else (signal.signal_score if signal else None)
    attention_score = metric.attention_score if metric else None
    market_significance = metric.market_significance if metric else None
    confidence = metric.data_confidence if metric else (signal.confidence if signal else None)
    confidence_text = confidence_label(confidence)
    signal_reason = metric.signal_reason if metric else (signal.signal_reason if signal else None)
    why_it_moved = _parse_why_it_moved(metric.why_it_moved if metric else None)

    if market.current_probability is not None and snapshots:
        history_points = [
            PricePoint(timestamp=_ensure_utc(snapshot.captured_at), price=snapshot.probability)
            for snapshot in snapshots
        ]
        live_changes = compute_probability_changes(market.current_probability, history_points, now=now)
        change_1h = change_1h if change_1h is not None else live_changes.change_1h
        change_24h = change_24h if change_24h is not None else live_changes.change_24h
        change_7d = change_7d if change_7d is not None else live_changes.change_7d

    components = None
    if metric is not None:
        components = SignalComponents(
            probability=metric.probability_component,
            volume=metric.volume_component,
            liquidity=metric.liquidity_component,
            persistence=metric.persistence_component,
        )
    elif signal is not None:
        components = SignalComponents(
            probability=signal.probability_component,
            volume=signal.volume_component,
            liquidity=signal.liquidity_component,
            persistence=signal.persistence_component,
        )

    has_24h = metric.has_24h_history if metric else coverage_hours >= 24
    has_7d = metric.has_7d_history if metric else coverage_hours >= 168
    market_status, resolves_in_days = _market_status(market, now=now)
    last_synced_at = metric.computed_at if metric else market.updated_at

    return MarketDetail(
        id=market.id,
        title=market.title,
        slug=market.slug,
        probability=market.current_probability,
        change1h=change_1h,
        change24h=change_24h,
        change7d=change_7d,
        change7d_unavailable_reason=_change7d_unavailable_reason(market, change_7d),
        volume=market.volume_24h,
        volume_1wk=market.volume_1wk,
        volume_spike=volume_spike,
        liquidity=market.liquidity,
        signal_score=signal_score,
        attention_score=attention_score,
        market_significance=market_significance,
        confidence=confidence,
        confidence_label=confidence_text,
        signal_reason=signal_reason,
        why_it_moved=why_it_moved,
        signal_components=components,
        category=market.category,
        image_url=market.image_url,
        end_date=market.end_date,
        updated_at=market.updated_at,
        last_synced_at=last_synced_at,
        polymarket_url=_build_polymarket_url(market),
        market_status=market_status,
        resolves_in_days=resolves_in_days,
        history_coverage_hours=round(
            metric.history_coverage_hours if metric and metric.history_coverage_hours else coverage_hours,
            1,
        ),
        has_24h_history=has_24h,
        has_7d_history=has_7d,
        history=history,
    )
