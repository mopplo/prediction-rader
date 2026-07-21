from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Market, MarketMetric, MarketSnapshot, Narrative, NarrativeMember, Signal
from app.services.narratives import aggregate_narratives, narrative_context_for_market
from app.services.polymarket import PolymarketClient, PricePoint, compute_probability_changes
from app.services.signals import (
    build_signal_metrics,
    evaluate_market_eligibility,
    rank_daily_radar,
    rank_emerging_signals,
    rank_top_movers,
)

logger = logging.getLogger(__name__)

SYNC_LOCK_KEY = 8675309


class SyncService:
    def __init__(self, db: Session, client: PolymarketClient | None = None) -> None:
        self.db = db
        self.client = client or PolymarketClient()
        self.settings = get_settings()
        self._pending_snapshot_keys: set[tuple[str, datetime]] = set()

    async def run(self) -> dict[str, int | dict[str, int] | str]:
        if not self._acquire_sync_lock():
            logger.warning("Another sync is already running; skipping this cycle")
            return {"status": "skipped", "reason": "sync_locked"}

        try:
            return await self._run_sync()
        finally:
            self._release_sync_lock()

    async def _run_sync(self) -> dict[str, int | dict[str, int]]:
        markets = await self.client.fetch_active_markets()
        token_ids = [market.yes_token_id for market in markets if market.yes_token_id]
        history_map = await self.client.fetch_batch_price_history(token_ids, interval="1w", fidelity=60)

        now = datetime.now(tz=UTC)
        candidates: list[dict] = []
        synced_markets = 0
        seen_market_ids: set[str] = set()
        filter_stats = {
            "total": len(markets),
            "eligible": 0,
            "excluded_short_cycle": 0,
            "excluded_other": 0,
        }

        for parsed in markets:
            if not parsed.yes_token_id or parsed.id in seen_market_ids:
                continue
            seen_market_ids.add(parsed.id)

            history = history_map.get(parsed.yes_token_id, [])
            if parsed.current_probability is None and history:
                parsed.current_probability = history[-1].price

            if parsed.current_probability is None:
                continue

            changes = compute_probability_changes(
                parsed.current_probability,
                history,
                now=now,
                max_deviation_hours=self.settings.history_max_deviation_hours,
            )
            eligibility = evaluate_market_eligibility(parsed, changes=changes, settings=self.settings, now=now)

            if eligibility.eligible:
                filter_stats["eligible"] += 1
            elif "short-cycle" in eligibility.reason.lower():
                filter_stats["excluded_short_cycle"] += 1
            else:
                filter_stats["excluded_other"] += 1

            candidates.append(
                {
                    "market": parsed,
                    "eligible": eligibility.eligible,
                    "eligibility_reason": eligibility.reason,
                    "computed_at": now,
                }
            )

        preliminary_narratives = aggregate_narratives(candidates, settings=self.settings, limit=999)

        for candidate in candidates:
            parsed = candidate["market"]
            history = history_map.get(parsed.yes_token_id, [])
            narrative_context = narrative_context_for_market(parsed.id, preliminary_narratives)
            metrics = build_signal_metrics(
                market=parsed,
                history=history,
                now=now,
                settings=self.settings,
                narrative_context=narrative_context,
                eligible=candidate["eligible"],
            )

            market = self._upsert_market(parsed, candidate["eligible"], candidate["eligibility_reason"])
            self._upsert_market_metric(market.id, metrics, now)
            self._backfill_clob_history(market, history)
            self._create_snapshot(market, parsed.current_probability, parsed.volume_24h, parsed.liquidity, now)
            synced_markets += 1

            candidate.update(
                {
                    "change_1h": metrics.change_1h,
                    "change_24h": metrics.change_24h,
                    "change_7d": metrics.change_7d,
                    "volume_spike": metrics.volume_spike,
                    "signal_score": metrics.signal_score,
                    "attention_score": metrics.attention_score,
                    "market_significance": metrics.market_significance,
                    "confidence": metrics.confidence,
                    "signal_reason": metrics.signal_reason,
                    "why_it_moved": metrics.why_it_moved,
                    "probability_component": metrics.probability_component,
                    "volume_component": metrics.volume_component,
                    "liquidity_component": metrics.liquidity_component,
                    "persistence_component": metrics.persistence_component,
                    "has_24h_history": metrics.has_24h_history,
                    "has_7d_history": metrics.has_7d_history,
                    "history_coverage_hours": metrics.history_coverage_hours,
                    "volume_24h": parsed.volume_24h,
                }
            )

        narratives = aggregate_narratives(candidates, settings=self.settings, limit=999)
        self._replace_narratives(narratives, now)
        self._replace_signals(candidates, now)
        self.db.commit()

        top_movers = rank_top_movers(candidates, settings=self.settings, limit=999)
        emerging = rank_emerging_signals(candidates, settings=self.settings, limit=999)
        daily = rank_daily_radar(candidates, settings=self.settings, limit=999)

        logger.info(
            "Sync stats: synced=%s eligible=%s top_movers=%s emerging=%s daily=%s narratives=%s filters=%s",
            synced_markets,
            filter_stats["eligible"],
            len(top_movers),
            len(emerging),
            len(daily),
            len(narratives),
            filter_stats,
        )

        return {
            "synced_markets": synced_markets,
            "top_movers": len(top_movers),
            "emerging_signals": len(emerging),
            "daily_radar": len(daily),
            "narratives": len(narratives),
            "filter_stats": filter_stats,
        }

    def _acquire_sync_lock(self) -> bool:
        try:
            locked = self.db.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": SYNC_LOCK_KEY})
            return bool(locked)
        except Exception:
            dialect = self.db.bind.dialect.name if self.db.bind is not None else ""
            if dialect == "postgresql":
                logger.exception("Failed to acquire PostgreSQL advisory lock; failing closed")
                return False
            return True

    def _release_sync_lock(self) -> None:
        try:
            self.db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": SYNC_LOCK_KEY})
        except Exception:
            return None

    def _upsert_market(self, parsed, eligible: bool, eligibility_reason: str) -> Market:
        market = self.db.get(Market, parsed.id)
        if market is None:
            market = Market(id=parsed.id)
            self.db.add(market)

        market.slug = parsed.slug
        market.title = parsed.title
        market.yes_token_id = parsed.yes_token_id
        market.current_probability = parsed.current_probability
        market.volume_24h = parsed.volume_24h
        market.volume_1wk = parsed.volume_1wk
        market.liquidity = parsed.liquidity
        market.category = parsed.category
        market.condition_id = parsed.condition_id
        market.group_item_id = parsed.group_item_id
        market.topic_key = parsed.topic_key
        market.event_id = parsed.event_id
        market.event_slug = parsed.event_slug
        market.event_title = parsed.event_title
        market.tags = json.dumps(parsed.tags)
        market.market_created_at = parsed.created_at
        market.eligibility_status = "eligible" if eligible else "excluded"
        market.eligibility_reason = eligibility_reason
        market.image_url = parsed.image_url
        market.end_date = parsed.end_date
        market.is_active = parsed.is_active
        market.is_closed = parsed.is_closed
        market.updated_at = datetime.now(tz=UTC)
        return market

    def _upsert_market_metric(self, market_id: str, metrics, computed_at: datetime) -> None:
        record = self.db.get(MarketMetric, market_id)
        if record is None:
            record = MarketMetric(market_id=market_id)
            self.db.add(record)

        record.change_1h = metrics.change_1h
        record.change_24h = metrics.change_24h
        record.change_7d = metrics.change_7d
        record.volume_spike = metrics.volume_spike
        record.signal_score = metrics.signal_score
        record.attention_score = metrics.attention_score
        record.market_significance = metrics.market_significance
        record.data_confidence = metrics.confidence
        record.signal_reason = metrics.signal_reason
        record.why_it_moved = json.dumps(metrics.why_it_moved)
        record.probability_component = metrics.probability_component
        record.volume_component = metrics.volume_component
        record.liquidity_component = metrics.liquidity_component
        record.persistence_component = metrics.persistence_component
        record.has_24h_history = metrics.has_24h_history
        record.has_7d_history = metrics.has_7d_history
        record.history_coverage_hours = metrics.history_coverage_hours
        record.eligible = metrics.eligible
        record.computed_at = computed_at

    def _round_snapshot_time(self, captured_at: datetime) -> datetime:
        return captured_at.replace(minute=(captured_at.minute // 15) * 15, second=0, microsecond=0)

    def _find_snapshot(self, market_id: str, captured_at: datetime) -> MarketSnapshot | None:
        key = (market_id, captured_at)
        if key in self._pending_snapshot_keys:
            for obj in self.db.new:
                if (
                    isinstance(obj, MarketSnapshot)
                    and obj.market_id == market_id
                    and obj.captured_at == captured_at
                ):
                    return obj

        return self.db.scalar(
            select(MarketSnapshot).where(
                MarketSnapshot.market_id == market_id,
                MarketSnapshot.captured_at == captured_at,
            )
        )

    def _remember_snapshot(self, market_id: str, captured_at: datetime) -> None:
        self._pending_snapshot_keys.add((market_id, captured_at))

    def _backfill_clob_history(self, market: Market, history: list[PricePoint]) -> None:
        seen: set[datetime] = set()
        for point in history:
            captured_at = self._round_snapshot_time(point.timestamp)
            if captured_at in seen:
                continue
            seen.add(captured_at)
            existing = self._find_snapshot(market.id, captured_at)
            if existing:
                existing.probability = point.price
                continue

            self.db.add(
                MarketSnapshot(
                    market_id=market.id,
                    probability=point.price,
                    volume_24h=None,
                    liquidity=market.liquidity,
                    captured_at=captured_at,
                )
            )
            self._remember_snapshot(market.id, captured_at)

    def _create_snapshot(
        self,
        market: Market,
        probability: float,
        volume_24h: float | None,
        liquidity: float | None,
        captured_at: datetime,
    ) -> None:
        rounded = self._round_snapshot_time(captured_at)
        existing = self._find_snapshot(market.id, rounded)
        if existing:
            existing.probability = probability
            existing.volume_24h = volume_24h
            existing.liquidity = liquidity
            return

        self.db.add(
            MarketSnapshot(
                market_id=market.id,
                probability=probability,
                volume_24h=volume_24h,
                liquidity=liquidity,
                captured_at=rounded,
            )
        )
        self._remember_snapshot(market.id, rounded)

    def _replace_narratives(self, narratives, computed_at: datetime) -> None:
        self.db.execute(delete(NarrativeMember))
        self.db.execute(delete(Narrative))

        for narrative in narratives:
            record = Narrative(
                topic_key=narrative.topic_key,
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
                computed_at=computed_at,
            )
            self.db.add(record)
            self.db.flush()
            for market_id in narrative.member_market_ids:
                self.db.add(NarrativeMember(narrative_id=record.id, market_id=market_id))

    def _replace_signals(self, candidates: list[dict], computed_at: datetime) -> None:
        top_movers = rank_top_movers(candidates, settings=self.settings)
        emerging = rank_emerging_signals(candidates, settings=self.settings)
        daily = rank_daily_radar(candidates, settings=self.settings)

        for signal_type in ("top_mover", "emerging", "daily_radar"):
            self.db.execute(delete(Signal).where(Signal.signal_type == signal_type))

        for candidate in top_movers:
            self._add_signal(candidate, "top_mover", computed_at)
        for candidate in emerging:
            self._add_signal(candidate, "emerging", computed_at)
        for candidate in daily:
            self._add_signal(candidate, "daily_radar", computed_at)

    def _add_signal(self, candidate: dict, signal_type: str, computed_at: datetime) -> None:
        market = candidate["market"]
        reason = candidate.get("signal_reason")
        if signal_type == "top_mover":
            reason = candidate.get("signal_reason") or f"Top mover: 24h change {candidate.get('change_24h', 0) * 100:.1f}pp"
        elif signal_type == "emerging":
            reason = candidate.get("signal_reason") or "Emerging attention signal"

        self.db.add(
            Signal(
                market_id=market.id,
                signal_type=signal_type,
                change_1h=candidate["change_1h"],
                change_24h=candidate["change_24h"],
                change_7d=candidate["change_7d"],
                volume_spike=candidate["volume_spike"],
                signal_score=candidate["signal_score"],
                confidence=candidate["confidence"],
                signal_reason=reason,
                probability_component=candidate["probability_component"],
                volume_component=candidate["volume_component"],
                liquidity_component=candidate["liquidity_component"],
                persistence_component=candidate["persistence_component"],
                computed_at=computed_at,
            )
        )


def run_sync(db: Session) -> dict[str, int | dict[str, int] | str]:
    service = SyncService(db)
    return asyncio.run(service.run())
