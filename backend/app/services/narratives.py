from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import UTC, datetime

from app.config import Settings, get_settings


@dataclass
class NarrativeAggregate:
    topic_key: str
    title: str
    category: str | None
    market_count: int
    active_count: int
    median_abs_change_24h: float | None
    aggregate_volume_spike: float | None
    direction_coherence: float | None
    dominant_direction: str | None
    narrative_score: float
    representative_market_id: str
    summary: str
    member_market_ids: list[str]


def _dominant_direction(changes: list[float]) -> tuple[str | None, float]:
    if not changes:
        return None, 0.0

    positive = sum(1 for value in changes if value > 0)
    negative = sum(1 for value in changes if value < 0)
    total = len(changes)
    if total == 0:
        return None, 0.0

    if positive >= negative:
        coherence = positive / total
        return ("higher" if positive > negative else "mixed"), coherence
    coherence = negative / total
    return ("lower" if negative > positive else "mixed"), coherence


def _is_active(candidate: dict) -> bool:
    change = candidate.get("change_24h")
    spike = candidate.get("volume_spike")
    return (change is not None and abs(change) >= 0.03) or (spike is not None and spike >= 1.5)


def build_narrative_summary(
    *,
    active_count: int,
    market_count: int,
    median_abs_change: float | None,
    aggregate_spike: float | None,
    dominant_direction: str | None,
    direction_coherence: float | None,
    min_coherence: float,
) -> str:
    parts: list[str] = [f"{active_count}/{market_count} markets active"]
    if median_abs_change is not None:
        parts.append(f"median |24h move| {median_abs_change * 100:.1f}pp")
    if aggregate_spike is not None:
        parts.append(f"aggregate volume {aggregate_spike:.1f}x baseline")
    if direction_coherence is not None and direction_coherence >= min_coherence and dominant_direction:
        parts.append(f"direction {dominant_direction}")
    else:
        parts.append("direction mixed")
    return "; ".join(parts)


def aggregate_narratives(
    candidates: list[dict],
    *,
    settings: Settings | None = None,
    limit: int | None = None,
) -> list[NarrativeAggregate]:
    settings = settings or get_settings()
    limit = limit or settings.narrative_trends_limit

    grouped: dict[str, list[dict]] = {}
    for candidate in candidates:
        if not candidate.get("eligible"):
            continue
        market = candidate["market"]
        topic_key = market.topic_key
        if not topic_key:
            continue
        grouped.setdefault(topic_key, []).append(candidate)

    narratives: list[NarrativeAggregate] = []
    for topic_key, members in grouped.items():
        if len(members) < settings.min_narrative_members:
            continue

        active_members = [member for member in members if _is_active(member)]
        if len(active_members) < 1:
            continue

        changes = [member["change_24h"] for member in members if member.get("change_24h") is not None]
        spikes = [member["volume_spike"] for member in members if member.get("volume_spike") is not None]
        median_abs = statistics.median([abs(value) for value in changes]) if changes else None
        aggregate_spike = statistics.median(spikes) if spikes else None
        dominant_direction, coherence = _dominant_direction(changes)

        representative = max(
            members,
            key=lambda item: (
                item.get("signal_score") or 0,
                item.get("confidence") or 0,
                item.get("market_significance") or 0,
            ),
        )
        rep_market = representative["market"]
        title = rep_market.event_title or rep_market.title
        category = rep_market.category

        score = 0.0
        score += min(len(active_members), 10) * 8
        if median_abs is not None:
            score += min(median_abs, 0.30) / 0.30 * 35
        if aggregate_spike is not None:
            score += min(aggregate_spike, 4.0) / 4.0 * 25
        if coherence is not None:
            score += coherence * 20
        score += (representative.get("confidence") or 0) * 0.12

        summary = build_narrative_summary(
            active_count=len(active_members),
            market_count=len(members),
            median_abs_change=median_abs,
            aggregate_spike=aggregate_spike,
            dominant_direction=dominant_direction,
            direction_coherence=coherence,
            min_coherence=settings.min_narrative_coherence,
        )

        narratives.append(
            NarrativeAggregate(
                topic_key=topic_key,
                title=title,
                category=category,
                market_count=len(members),
                active_count=len(active_members),
                median_abs_change_24h=median_abs,
                aggregate_volume_spike=aggregate_spike,
                direction_coherence=coherence,
                dominant_direction=dominant_direction,
                narrative_score=round(min(score, 100), 2),
                representative_market_id=rep_market.id,
                summary=summary,
                member_market_ids=[member["market"].id for member in members],
            )
        )

    narratives.sort(
        key=lambda item: (
            item.narrative_score,
            item.active_count,
            item.median_abs_change_24h or 0,
        ),
        reverse=True,
    )
    return narratives[:limit]


def narrative_context_for_market(
    market_id: str,
    narratives: list[NarrativeAggregate],
) -> dict | None:
    for narrative in narratives:
        if market_id in narrative.member_market_ids:
            return {
                "active_count": narrative.active_count,
                "direction_coherence": narrative.direction_coherence,
                "dominant_direction": narrative.dominant_direction,
            }
    return None
