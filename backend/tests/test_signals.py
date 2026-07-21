import pytest
from datetime import UTC, datetime, timedelta

from app.services.polymarket import ParsedMarket, PricePoint, compute_topic_key
from app.services.signals import (
    build_signal_metrics,
    confidence_label,
    compute_attention_score,
    compute_market_significance,
    evaluate_market_eligibility,
    rank_daily_radar,
    rank_emerging_signals,
    rank_top_movers,
)
from app.services.narratives import aggregate_narratives


def make_market(**overrides) -> ParsedMarket:
    defaults = {
        "id": "market-1",
        "slug": "gpt-6",
        "title": "Will GPT-6 be released before 2027?",
        "yes_token_id": "token",
        "current_probability": 0.58,
        "volume_24h": 50000,
        "volume_1wk": 210000,
        "liquidity": 20000,
        "category": "AI",
        "image_url": None,
        "end_date": datetime(2027, 1, 1, tzinfo=UTC),
        "condition_id": "cond-1",
        "group_item_id": None,
        "topic_key": "event:event-1",
        "event_id": "event-1",
        "event_title": "AI",
        "tags": ["ai", "technology"],
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return ParsedMarket(**defaults)


def test_evaluate_market_eligibility_rejects_short_cycle() -> None:
    market = make_market(title="LoL: Gen.G vs T1 (BO1)", tags=["esports"], category="Sports")
    result = evaluate_market_eligibility(market)
    assert result.eligible is False


def test_evaluate_market_eligibility_rejects_near_settlement_probability() -> None:
    market = make_market(current_probability=0.96)
    result = evaluate_market_eligibility(market)
    assert result.eligible is False
    assert "Probability near settlement" in result.reason


def test_rank_top_movers_applies_quality_gates() -> None:
    candidates = [
        {
            "market": make_market(id="1"),
            "eligible": True,
            "change_24h": 0.2,
            "signal_score": 80,
            "confidence": 70,
            "market_significance": 60,
        },
        {
            "market": make_market(id="2"),
            "eligible": True,
            "change_24h": 0.02,
            "signal_score": 90,
            "confidence": 80,
            "market_significance": 70,
        },
    ]

    ranked = rank_top_movers(candidates, limit=2)
    assert len(ranked) == 1
    assert ranked[0]["market"].id == "1"


def test_rank_emerging_signals_uses_attention_score() -> None:
    candidates = [
        {
            "market": make_market(id="1", event_id="event-1"),
            "eligible": True,
            "change_24h": 0.05,
            "volume_spike": 2.5,
            "attention_score": 55,
            "signal_score": 40,
            "confidence": 70,
        },
        {
            "market": make_market(id="2", event_id="event-2"),
            "eligible": True,
            "change_24h": 0.06,
            "volume_spike": 3.0,
            "attention_score": 80,
            "signal_score": 60,
            "confidence": 70,
        },
    ]

    ranked = rank_emerging_signals(candidates, limit=2)
    assert ranked[0]["market"].id == "2"
    assert ranked[0]["attention_score"] == 80


def test_rank_daily_radar_applies_diversity() -> None:
    today = datetime.now(tz=UTC)
    candidates = [
        {
            "market": make_market(id="1", event_id="event-1", category="AI"),
            "eligible": True,
            "signal_score": 90,
            "confidence": 80,
            "change_24h": 0.1,
            "market_significance": 70,
            "computed_at": today,
        },
        {
            "market": make_market(id="2", event_id="event-1", category="AI"),
            "eligible": True,
            "signal_score": 85,
            "confidence": 80,
            "change_24h": 0.08,
            "market_significance": 65,
            "computed_at": today,
        },
    ]

    ranked = rank_daily_radar(candidates, limit=5)
    assert len(ranked) == 1


def test_build_signal_metrics_is_bounded() -> None:
    now = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    history = [
        PricePoint(timestamp=now - timedelta(hours=30), price=0.42),
        PricePoint(timestamp=now - timedelta(days=8), price=0.35),
    ]
    market = make_market()

    metrics = build_signal_metrics(market=market, history=history, now=now)

    assert 0 <= metrics.signal_score <= 100
    assert 0 <= metrics.attention_score <= 100
    assert 0 <= metrics.market_significance <= 100
    assert metrics.confidence >= 40
    assert "24h probability" in metrics.signal_reason
    assert len(metrics.why_it_moved) >= 3
    assert metrics.has_7d_history is True


def test_compute_attention_score_weights_volume_highest() -> None:
    volume_led = compute_attention_score(
        change_24h=0.05,
        volume_spike=4.0,
        volume_24h=100000,
        liquidity=20000,
    )
    prob_led = compute_attention_score(
        change_24h=0.25,
        volume_spike=1.2,
        volume_24h=100000,
        liquidity=20000,
    )
    assert volume_led > prob_led


def test_confidence_label_boundaries() -> None:
    assert confidence_label(90) == "Very High"
    assert confidence_label(89) == "High"
    assert confidence_label(70) == "High"
    assert confidence_label(69) == "Medium"
    assert confidence_label(50) == "Medium"
    assert confidence_label(49) == "Low"


def test_compute_topic_key_prefers_event_then_group() -> None:
    assert compute_topic_key(event_id="e1", group_item_id="g1", title="Foo") == "event:e1"
    assert compute_topic_key(event_id=None, group_item_id="g1", title="Foo") == "group:g1"


def test_candidate_key_groups_title_family() -> None:
    from app.services.signals import _candidate_key

    candidate_a = {
        "market": make_market(
            id="1",
            event_id=None,
            group_item_id=None,
            topic_key="title:israel x iran ceasefire continues through ?",
            title="Israel x Iran ceasefire continues through July 31?",
        )
    }
    candidate_b = {
        "market": make_market(
            id="2",
            event_id=None,
            group_item_id=None,
            topic_key="title:israel x iran ceasefire continues through ?",
            title="Israel x Iran ceasefire continues through July 25?",
        )
    }

    assert _candidate_key(candidate_a) == _candidate_key(candidate_b)


def test_aggregate_narratives_marks_mixed_direction() -> None:
    market_a = make_market(id="a", event_id="event-a", topic_key="event:event-a")
    market_b = make_market(id="b", event_id="event-a", topic_key="event:event-a", title="Related market B")
    candidates = [
        {
            "market": market_a,
            "eligible": True,
            "change_24h": 0.08,
            "volume_spike": 2.0,
            "signal_score": 70,
            "confidence": 75,
            "market_significance": 60,
        },
        {
            "market": market_b,
            "eligible": True,
            "change_24h": -0.06,
            "volume_spike": 1.8,
            "signal_score": 65,
            "confidence": 70,
            "market_significance": 55,
        },
    ]

    narratives = aggregate_narratives(candidates, limit=5)
    assert len(narratives) == 1
    assert narratives[0].dominant_direction == "mixed"
    assert "mixed" in narratives[0].summary.lower()


def test_compute_market_significance_is_bounded() -> None:
    score = compute_market_significance(make_market())
    assert 0 <= score <= 100
