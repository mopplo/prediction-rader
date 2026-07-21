import pytest
from datetime import UTC, datetime, timedelta

from app.services.polymarket import (
    PolymarketClient,
    ParsedMarket,
    PricePoint,
    compute_probability_changes,
    compute_topic_key,
    compute_volume_spike,
    is_information_market,
    is_short_cycle_market,
    probability_at_or_before,
)


@pytest.fixture
def client() -> PolymarketClient:
    return PolymarketClient()


def test_parse_market_extracts_probability_and_token(client: PolymarketClient) -> None:
    parsed = client._parse_market(
        {
            "id": "123",
            "question": "Will BTC exceed $200k by 2027?",
            "slug": "btc-200k",
            "clobTokenIds": '["token-yes", "token-no"]',
            "outcomePrices": '["0.58", "0.42"]',
            "volume24hr": 1200000,
            "volume1wk": 7000000,
            "events": [{"id": "event-1", "title": "Crypto", "category": "Crypto", "tags": [{"label": "Crypto"}]}],
        }
    )

    assert parsed is not None
    assert parsed.id == "123"
    assert parsed.yes_token_id == "token-yes"
    assert parsed.current_probability == pytest.approx(0.58)
    assert parsed.volume_24h == pytest.approx(1200000)
    assert parsed.event_id == "event-1"
    assert parsed.event_slug is None
    assert parsed.topic_key == "event:event-1"
    assert "crypto" in parsed.tags


def test_parse_market_extracts_group_item_and_condition() -> None:
    client = PolymarketClient()
    parsed = client._parse_market(
        {
            "id": "456",
            "question": "Will inflation fall below 2%?",
            "conditionId": "cond-456",
            "groupItemId": "group-789",
            "clobTokenIds": '["token-yes"]',
            "outcomePrices": '["0.44"]',
        }
    )
    assert parsed is not None
    assert parsed.condition_id == "cond-456"
    assert parsed.group_item_id == "group-789"
    assert parsed.topic_key == "group:group-789"


def test_parse_market_extracts_event_slug_and_status() -> None:
    client = PolymarketClient()
    parsed = client._parse_market(
        {
            "id": "789",
            "question": "Will Bitcoin exceed $150k in 2026?",
            "slug": "market-level-slug",
            "active": True,
            "closed": False,
            "clobTokenIds": '["token-yes"]',
            "outcomePrices": '["0.61"]',
            "events": [
                {"id": "event-2", "slug": "bitcoin-150k-2026", "title": "Bitcoin Price"}
            ],
        }
    )
    assert parsed is not None
    assert parsed.event_slug == "bitcoin-150k-2026"
    assert parsed.is_active is True
    assert parsed.is_closed is False


def test_compute_topic_key_title_family() -> None:
    key_a = compute_topic_key(
        event_id=None,
        group_item_id=None,
        title="Israel x Iran ceasefire continues through July 31?",
    )
    key_b = compute_topic_key(
        event_id=None,
        group_item_id=None,
        title="Israel x Iran ceasefire continues through July 25?",
    )
    assert key_a == key_b


def test_probability_at_or_before_rejects_stale_point() -> None:
    now = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    points = [PricePoint(timestamp=now - timedelta(hours=48), price=0.4)]

    price, valid = probability_at_or_before(
        points,
        now - timedelta(hours=24),
        max_deviation=timedelta(hours=6),
    )

    assert price is None
    assert valid is False


def test_compute_probability_changes_requires_coverage() -> None:
    now = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    history = [PricePoint(timestamp=now - timedelta(hours=2), price=0.42)]

    changes = compute_probability_changes(0.58, history, now=now)

    assert changes.change_1h == pytest.approx(0.16)
    assert changes.change_24h is None
    assert changes.has_24h_history is False


def test_compute_volume_spike_excludes_current_day() -> None:
    assert compute_volume_spike(140000, 700000) == pytest.approx(140000 / ((700000 - 140000) / 6))


def test_compute_volume_spike_requires_market_age() -> None:
    now = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)
    created = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
    assert compute_volume_spike(140000, 700000, market_created_at=created, now=now) is None


def test_history_coverage_hours() -> None:
    from app.services.polymarket import history_coverage_hours

    now = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)
    history = [PricePoint(timestamp=now - timedelta(days=3), price=0.5)]
    assert history_coverage_hours(history, now=now) == pytest.approx(72.0)


def test_short_cycle_market_detection() -> None:
    assert is_short_cycle_market("LoL: Gen.G vs T1 (BO1)", ["esports"]) is True
    assert is_short_cycle_market("Bitcoin Up or Down on July 21?", []) is True
    assert is_short_cycle_market("Estoril Open: Botic van de Zandschulp vs Jaime Faria", ["tennis"]) is True
    assert is_short_cycle_market("Will GPT-6 be released before 2027?", ["ai"]) is False


def test_information_market_detection() -> None:
    assert is_information_market("Will the Fed cut rates in 2026?", ["economy"], "Macro") is True
    assert is_information_market("LoL: Gen.G vs T1 (BO1)", ["esports"], "Sports") is False
