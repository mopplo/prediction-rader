from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.config import Settings, get_settings
from app.services.polymarket import (
    ParsedMarket,
    ProbabilityChanges,
    compute_probability_changes,
    compute_topic_key,
    compute_volume_spike,
    history_coverage_hours,
    is_information_market,
    is_short_cycle_market,
    normalize_title_family,
)


@dataclass
class EligibilityResult:
    eligible: bool
    reason: str


@dataclass
class SignalMetrics:
    change_1h: float | None
    change_24h: float | None
    change_7d: float | None
    volume_spike: float | None
    signal_score: float
    attention_score: float
    market_significance: float
    confidence: float
    signal_reason: str
    why_it_moved: list[str]
    probability_component: float
    volume_component: float
    liquidity_component: float
    persistence_component: float
    has_24h_history: bool = False
    has_7d_history: bool = False
    history_coverage_hours: float = 0.0
    eligible: bool = False


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def winsorize_abs(value: float | None, cap: float) -> float:
    if value is None:
        return 0.0
    return min(abs(value), cap) / cap * 100


def bounded_log_spike(volume_spike: float | None, cap: float = 4.0) -> float:
    if volume_spike is None or volume_spike <= 1:
        return 0.0
    transformed = math.log1p(volume_spike - 1)
    max_transformed = math.log1p(cap)
    if max_transformed <= 0:
        return 0.0
    return clamp(transformed / max_transformed * 100)


def liquidity_score(volume_24h: float | None, liquidity: float | None) -> float:
    volume = volume_24h or 0.0
    depth = liquidity or 0.0
    volume_part = clamp(math.log10(max(volume, 1)) / 6 * 100)
    liquidity_part = clamp(math.log10(max(depth, 1)) / 5 * 100)
    return volume_part * 0.6 + liquidity_part * 0.4


def persistence_score(change_1h: float | None, change_24h: float | None) -> float:
    if change_1h is None or change_24h is None:
        return 0.0
    if change_1h == 0 or change_24h == 0:
        return 20.0
    same_direction = (change_1h > 0 and change_24h > 0) or (change_1h < 0 and change_24h < 0)
    if not same_direction:
        return 10.0
    ratio = min(abs(change_1h), abs(change_24h)) / max(abs(change_1h), abs(change_24h))
    return clamp(40 + ratio * 60)


def evaluate_market_eligibility(
    market: ParsedMarket,
    *,
    changes: ProbabilityChanges | None = None,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> EligibilityResult:
    settings = settings or get_settings()
    now = now or datetime.now(tz=UTC)

    if is_short_cycle_market(market.title, market.tags):
        return EligibilityResult(False, "Excluded short-cycle market")

    if not is_information_market(market.title, market.tags, market.category):
        return EligibilityResult(False, "Not an information-market category")

    probability = market.current_probability
    if probability is not None and (
        probability <= settings.min_probability or probability >= settings.max_probability
    ):
        return EligibilityResult(False, "Probability near settlement")

    if market.end_date and market.end_date <= now:
        return EligibilityResult(False, "Market already ended")

    if market.end_date and market.end_date - now < timedelta(hours=settings.min_hours_to_end):
        return EligibilityResult(False, "Market ending too soon")

    if (market.volume_24h or 0) < settings.min_volume_24h:
        return EligibilityResult(False, "Insufficient 24h volume")

    if (market.liquidity or 0) < settings.min_liquidity:
        return EligibilityResult(False, "Insufficient liquidity")

    if changes is not None and not changes.has_24h_history:
        return EligibilityResult(False, "Missing valid 24h history")

    return EligibilityResult(True, "Eligible")


def build_signal_reason(
    *,
    change_24h: float | None,
    volume_spike: float | None,
    signal_type: str,
) -> str:
    parts: list[str] = []
    if change_24h is not None:
        direction = "rose" if change_24h > 0 else "fell"
        parts.append(f"24h probability {direction} {abs(change_24h) * 100:.1f}pp")
    if volume_spike is not None:
        parts.append(f"volume is {volume_spike:.1f}x the prior 6-day daily average")
    if not parts:
        return "Signal passed quality checks"
    if signal_type == "emerging":
        return "Emerging attention: " + "; ".join(parts)
    if signal_type == "top_mover":
        return "Top mover: " + parts[0]
    return "; ".join(parts)


def compute_data_confidence(
    *,
    has_24h_history: bool,
    has_7d_history: bool,
    volume_spike: float | None,
    liquidity_component: float,
    persistence_component: float,
    history_coverage_hours: float,
) -> float:
    score = 20.0
    if has_24h_history:
        score += 25
    if has_7d_history:
        score += 20
    elif history_coverage_hours >= 72:
        score += 10
    if volume_spike is not None:
        score += 10
    score += liquidity_component * 0.15
    score += persistence_component * 0.1
    return round(clamp(score), 2)


def confidence_label(confidence: float | None) -> str | None:
    if confidence is None:
        return None
    if confidence >= 90:
        return "Very High"
    if confidence >= 70:
        return "High"
    if confidence >= 50:
        return "Medium"
    return "Low"


def compute_market_significance(
    market: ParsedMarket,
    *,
    now: datetime | None = None,
    settings: Settings | None = None,
) -> float:
    settings = settings or get_settings()
    now = now or datetime.now(tz=UTC)

    volume_part = clamp(math.log10(max(market.volume_24h or 0, 1)) / 6 * 100)
    liquidity_part = clamp(math.log10(max(market.liquidity or 0, 1)) / 5 * 100)
    coverage_part = 70.0 if market.event_id or market.group_item_id else 35.0

    time_part = 50.0
    if market.end_date and market.end_date > now:
        days_remaining = (market.end_date - now).total_seconds() / 86400
        time_part = clamp(min(days_remaining, 365) / 365 * 100)

    return round(volume_part * 0.35 + liquidity_part * 0.30 + coverage_part * 0.20 + time_part * 0.15, 2)


def compute_attention_score(
    *,
    change_24h: float | None,
    volume_spike: float | None,
    volume_24h: float | None,
    liquidity: float | None,
) -> float:
    volume_component = bounded_log_spike(volume_spike, cap=4.0) * 0.50
    probability_component = winsorize_abs(change_24h, cap=0.30) * 0.30
    liquidity_component = liquidity_score(volume_24h, liquidity) * 0.20
    return round(clamp(volume_component + probability_component + liquidity_component), 2)


def build_why_it_moved(
    *,
    market: ParsedMarket,
    change_24h: float | None,
    volume_spike: float | None,
    liquidity: float | None,
    confidence: float,
    has_24h_history: bool,
    has_7d_history: bool,
    narrative_context: dict | None = None,
) -> list[str]:
    reasons: list[str] = []

    if change_24h is not None and has_24h_history:
        direction = "rose" if change_24h > 0 else "fell"
        reasons.append(f"24h probability {direction} {abs(change_24h) * 100:.1f}pp")
    elif not has_24h_history:
        reasons.append("24h history insufficient for probability change")

    if volume_spike is not None:
        reasons.append(f"24h volume is {volume_spike:.1f}x the prior 6-day daily average")
    else:
        reasons.append("Volume baseline unavailable or history insufficient")

    if liquidity is not None and liquidity >= 5000:
        reasons.append(f"Liquidity depth ${liquidity:,.0f}")
    elif liquidity is not None:
        reasons.append(f"Low liquidity (${liquidity:,.0f})")
    else:
        reasons.append("Liquidity data unavailable")

    label = confidence_label(confidence) or "Unknown"
    reasons.append(f"{label} data confidence ({confidence:.0f})")

    if narrative_context:
        active_count = narrative_context.get("active_count", 0)
        coherence = narrative_context.get("direction_coherence")
        if active_count >= 2:
            if coherence is not None and coherence >= 0.6:
                direction = narrative_context.get("dominant_direction", "mixed")
                reasons.append(
                    f"{active_count} related markets active in same narrative ({direction})"
                )
            else:
                reasons.append(f"{active_count} related markets active with mixed direction")

    if not has_7d_history:
        reasons.append("7d history insufficient for longer-term context")

    return reasons


def compute_signal_score(
    *,
    change_24h: float | None,
    volume_spike: float | None,
    volume_24h: float | None,
    liquidity: float | None,
    change_1h: float | None,
) -> tuple[float, float, float, float, float]:
    probability_component = winsorize_abs(change_24h, cap=0.30) * 0.45
    volume_component = bounded_log_spike(volume_spike, cap=4.0) * 0.25
    liquidity_component = liquidity_score(volume_24h, liquidity) * 0.15
    persistence_component = persistence_score(change_1h, change_24h) * 0.15
    total = probability_component + volume_component + liquidity_component + persistence_component
    return (
        round(total, 2),
        round(probability_component / 0.45, 2) if probability_component else 0.0,
        round(volume_component / 0.25, 2) if volume_component else 0.0,
        round(liquidity_component / 0.15, 2) if liquidity_component else 0.0,
        round(persistence_component / 0.15, 2) if persistence_component else 0.0,
    )


def build_signal_metrics(
    *,
    market: ParsedMarket,
    history: list,
    now: datetime | None = None,
    signal_type: str = "daily_radar",
    settings: Settings | None = None,
    narrative_context: dict | None = None,
    eligible: bool | None = None,
) -> SignalMetrics:
    settings = settings or get_settings()
    now = now or datetime.now(tz=UTC)
    changes = compute_probability_changes(
        market.current_probability,
        history,
        now=now,
        max_deviation_hours=settings.history_max_deviation_hours,
    )
    volume_spike = compute_volume_spike(
        market.volume_24h,
        market.volume_1wk,
        market_created_at=market.created_at,
        now=now,
    )
    score, prob_c, vol_c, liq_c, persist_c = compute_signal_score(
        change_24h=changes.change_24h,
        volume_spike=volume_spike,
        volume_24h=market.volume_24h,
        liquidity=market.liquidity,
        change_1h=changes.change_1h,
    )
    attention = compute_attention_score(
        change_24h=changes.change_24h,
        volume_spike=volume_spike,
        volume_24h=market.volume_24h,
        liquidity=market.liquidity,
    )
    significance = compute_market_significance(market, now=now, settings=settings)
    coverage_hours = history_coverage_hours(history, now=now)
    confidence = compute_data_confidence(
        has_24h_history=changes.has_24h_history,
        has_7d_history=changes.has_7d_history,
        volume_spike=volume_spike,
        liquidity_component=liq_c,
        persistence_component=persist_c,
        history_coverage_hours=coverage_hours,
    )
    reason = build_signal_reason(
        change_24h=changes.change_24h,
        volume_spike=volume_spike,
        signal_type=signal_type,
    )
    why_it_moved = build_why_it_moved(
        market=market,
        change_24h=changes.change_24h,
        volume_spike=volume_spike,
        liquidity=market.liquidity,
        confidence=confidence,
        has_24h_history=changes.has_24h_history,
        has_7d_history=changes.has_7d_history,
        narrative_context=narrative_context,
    )
    is_eligible = (
        eligible
        if eligible is not None
        else evaluate_market_eligibility(market, changes=changes, settings=settings, now=now).eligible
    )
    return SignalMetrics(
        change_1h=changes.change_1h,
        change_24h=changes.change_24h,
        change_7d=changes.change_7d,
        volume_spike=volume_spike,
        signal_score=score,
        attention_score=attention,
        market_significance=significance,
        confidence=confidence,
        signal_reason=reason,
        why_it_moved=why_it_moved,
        probability_component=prob_c,
        volume_component=vol_c,
        liquidity_component=liq_c,
        persistence_component=persist_c,
        has_24h_history=changes.has_24h_history,
        has_7d_history=changes.has_7d_history,
        history_coverage_hours=coverage_hours,
        eligible=is_eligible,
    )


def _normalize_title_family(title: str) -> str:
    return normalize_title_family(title)


def _candidate_key(candidate: dict) -> str:
    market = candidate["market"]
    topic_key = market.topic_key or compute_topic_key(
        event_id=market.event_id,
        group_item_id=market.group_item_id,
        title=market.title,
        event_title=market.event_title,
    )
    return topic_key


def _apply_diversity(candidates: list[dict], *, limit: int, max_per_event: int = 1, max_per_category: int = 2) -> list[dict]:
    selected: list[dict] = []
    event_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for candidate in candidates:
        market = candidate["market"]
        event_key = _candidate_key(candidate)
        category_key = (market.category or "uncategorized").lower()

        if event_counts.get(event_key, 0) >= max_per_event:
            continue
        if category_counts.get(category_key, 0) >= max_per_category:
            continue

        selected.append(candidate)
        event_counts[event_key] = event_counts.get(event_key, 0) + 1
        category_counts[category_key] = category_counts.get(category_key, 0) + 1
        if len(selected) >= limit:
            break

    return selected


def rank_top_movers(candidates: list[dict], *, settings: Settings | None = None, limit: int | None = None) -> list[dict]:
    settings = settings or get_settings()
    limit = limit or settings.top_movers_limit
    filtered = [
        candidate
        for candidate in candidates
        if candidate.get("eligible")
        and candidate.get("change_24h") is not None
        and abs(candidate["change_24h"]) >= settings.min_change_24h
        and candidate.get("confidence", 0) >= settings.min_confidence
    ]
    filtered.sort(
        key=lambda item: (
            abs(item.get("change_24h") or 0),
            item.get("signal_score") or 0,
            item.get("confidence") or 0,
            item.get("market_significance") or 0,
        ),
        reverse=True,
    )
    return _apply_diversity(filtered, limit=limit)


def rank_emerging_signals(
    candidates: list[dict], *, settings: Settings | None = None, limit: int | None = None
) -> list[dict]:
    settings = settings or get_settings()
    limit = limit or settings.emerging_signals_limit
    filtered = [
        candidate
        for candidate in candidates
        if candidate.get("eligible")
        and candidate.get("volume_spike") is not None
        and candidate["volume_spike"] >= settings.min_volume_spike
        and abs(candidate.get("change_24h") or 0) >= settings.min_emerging_change_24h
        and candidate.get("confidence", 0) >= settings.min_confidence
    ]
    filtered.sort(
        key=lambda item: (
            item.get("attention_score") or 0,
            item.get("volume_spike") or 0,
            abs(item.get("change_24h") or 0),
        ),
        reverse=True,
    )
    return _apply_diversity(filtered, limit=limit)


def rank_daily_radar(candidates: list[dict], *, settings: Settings | None = None, limit: int | None = None) -> list[dict]:
    settings = settings or get_settings()
    limit = limit or settings.daily_radar_limit
    today = datetime.now(tz=UTC).date()
    filtered = [
        candidate
        for candidate in candidates
        if candidate.get("eligible")
        and candidate.get("computed_at")
        and candidate["computed_at"].date() == today
        and candidate.get("confidence", 0) >= settings.min_confidence
    ]
    filtered.sort(
        key=lambda item: (
            item.get("signal_score") or 0,
            item.get("confidence") or 0,
            item.get("market_significance") or 0,
            abs(item.get("change_24h") or 0),
        ),
        reverse=True,
    )
    return _apply_diversity(filtered, limit=limit, max_per_event=1, max_per_category=2)
