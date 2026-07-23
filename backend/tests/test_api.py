import pytest
from datetime import UTC, datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import Market, MarketMetric, MarketSnapshot, Narrative, Signal


@pytest.fixture()
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def seed_db() -> None:
        db = TestingSessionLocal()
        market = Market(
            id="market-1",
            title="Will GPT-6 be released before 2027?",
            slug="gpt-6-before-2027",
            category="AI",
            current_probability=0.68,
            volume_24h=850000,
            volume_1wk=4200000,
            liquidity=50000,
            eligibility_status="eligible",
            market_created_at=datetime(2026, 1, 1, tzinfo=UTC),
            topic_key="event:event-1",
            event_slug="gpt-6-release",
            is_active=True,
            is_closed=False,
            end_date=datetime(2026, 8, 1, tzinfo=UTC),
        )
        db.add(market)
        db.add(
            MarketMetric(
                market_id="market-1",
                change_24h=0.17,
                change_7d=0.22,
                volume_spike=2.1,
                signal_score=72.5,
                attention_score=68.0,
                market_significance=74.0,
                data_confidence=81.0,
                signal_reason="Top mover: 24h probability rose 17.0pp",
                why_it_moved='["24h probability rose 17.0pp", "Volume baseline unavailable"]',
                eligible=True,
                computed_at=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
            )
        )
        db.add(
            Signal(
                market_id="market-1",
                signal_type="top_mover",
                change_24h=0.17,
                change_7d=0.22,
                volume_spike=2.1,
                signal_score=72.5,
                confidence=81.0,
                signal_reason="Top mover: 24h probability rose 17.0pp",
                computed_at=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
            )
        )
        db.add(
            Narrative(
                topic_key="event:event-1",
                title="AI",
                category="AI",
                market_count=2,
                active_count=2,
                median_abs_change_24h=0.12,
                aggregate_volume_spike=2.0,
                direction_coherence=0.5,
                dominant_direction="mixed",
                narrative_score=65.0,
                representative_market_id="market-1",
                summary="2/2 markets active; direction mixed",
                computed_at=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
            )
        )
        db.commit()
        db.close()

    seed_db()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.testing_session_local = TestingSessionLocal  # type: ignore[attr-defined]
        yield test_client
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_radar_stats(client: TestClient) -> None:
    response = client.get("/api/stats")
    assert response.status_code == 200
    payload = response.json()
    assert payload["markets_tracked"] == 1
    assert payload["active_signals"] == 1
    assert payload["sync_interval_minutes"] == 120
    assert payload["last_synced_at"].startswith("2026-07-21T12:00:00")


def test_radar_stats_dedupes_active_signals_across_types(client: TestClient) -> None:
    session_factory = client.testing_session_local  # type: ignore[attr-defined]
    db = session_factory()
    db.add(
        Market(
            id="market-2",
            title="Will the Fed cut rates in 2026?",
            category="Macro",
            current_probability=0.42,
            volume_24h=500000,
            volume_1wk=2500000,
            eligibility_status="eligible",
        )
    )
    db.add(
        Signal(
            market_id="market-1",
            signal_type="emerging",
            change_24h=0.05,
            volume_spike=2.0,
            signal_score=60.0,
            confidence=75.0,
            signal_reason="Emerging attention",
            computed_at=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
        )
    )
    db.add(
        Signal(
            market_id="market-2",
            signal_type="daily_radar",
            change_24h=0.03,
            signal_score=50.0,
            confidence=70.0,
            signal_reason="Daily pick",
            computed_at=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
        )
    )
    db.commit()
    db.close()

    response = client.get("/api/stats")
    payload = response.json()
    assert payload["markets_tracked"] == 2
    assert payload["active_signals"] == 2


def test_radar_stats_empty(client: TestClient) -> None:
    session_factory = client.testing_session_local  # type: ignore[attr-defined]
    db = session_factory()
    db.query(Signal).delete()
    db.query(MarketMetric).delete()
    db.query(Narrative).delete()
    db.query(Market).delete()
    db.commit()
    db.close()

    response = client.get("/api/stats")
    assert response.status_code == 200
    payload = response.json()
    assert payload["markets_tracked"] == 0
    assert payload["active_signals"] == 0
    assert payload["last_synced_at"] is None
    assert payload["sync_interval_minutes"] == 120


def test_top_movers(client: TestClient) -> None:
    response = client.get("/api/top-movers")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "Will GPT-6 be released before 2027?"
    assert payload[0]["change24h"] == pytest.approx(0.17)
    assert payload[0]["confidence"] == pytest.approx(81.0)
    assert payload[0]["confidence_label"] == "High"
    assert payload[0]["market_significance"] == pytest.approx(74.0)
    assert payload[0]["polymarket_url"].endswith("/event/gpt-6-release")


def test_top_movers_uses_latest_batch_only(client: TestClient) -> None:
    session_factory = client.testing_session_local  # type: ignore[attr-defined]
    db = session_factory()
    db.add(
        Market(
            id="market-2",
            title="Will the Fed cut rates in 2026?",
            category="Macro",
            current_probability=0.42,
            volume_24h=500000,
            volume_1wk=2500000,
            eligibility_status="eligible",
        )
    )
    db.add(
        Signal(
            market_id="market-2",
            signal_type="top_mover",
            change_24h=0.08,
            signal_score=55.0,
            confidence=70.0,
            signal_reason="Stale batch market",
            computed_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )
    db.commit()
    db.close()

    response = client.get("/api/top-movers")
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "market-1"
    assert payload[0]["change24h"] == pytest.approx(0.17)


def test_narrative_trends(client: TestClient) -> None:
    response = client.get("/api/narrative-trends")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["title"] == "AI"
    assert payload[0]["dominant_direction"] == "mixed"


def test_market_detail_uses_market_metrics(client: TestClient) -> None:
    session_factory = client.testing_session_local  # type: ignore[attr-defined]
    db = session_factory()
    db.query(Signal).filter(Signal.market_id == "market-1").delete()
    db.query(MarketMetric).filter(MarketMetric.market_id == "market-1").update(
        {
            "probability_component": 80.0,
            "volume_component": 40.0,
            "liquidity_component": 70.0,
            "persistence_component": 55.0,
        }
    )
    db.add(
        MarketSnapshot(
            market_id="market-1",
            probability=0.60,
            volume_24h=1000,
            captured_at=datetime(2026, 7, 20, 12, 0, tzinfo=UTC),
        )
    )
    db.add(
        MarketSnapshot(
            market_id="market-1",
            probability=0.68,
            volume_24h=1200,
            captured_at=datetime(2026, 7, 21, 12, 0, tzinfo=UTC),
        )
    )
    db.commit()
    db.close()

    response = client.get("/api/market/market-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["signal_score"] == pytest.approx(72.5)
    assert payload["attention_score"] == pytest.approx(68.0)
    assert payload["market_significance"] == pytest.approx(74.0)
    assert payload["confidence_label"] == "High"
    assert payload["polymarket_url"].endswith("/event/gpt-6-release")
    assert payload["market_status"] == "open"
    assert payload["resolves_in_days"] is not None
    assert payload["last_synced_at"].startswith("2026-07-21T12:00:00")
    assert len(payload["why_it_moved"]) >= 1
    assert len(payload["history"]) == 2
    assert payload["signal_components"]["probability"] is not None


def test_market_detail_marks_closed_when_end_date_passed(client: TestClient) -> None:
    session_factory = client.testing_session_local  # type: ignore[attr-defined]
    db = session_factory()
    market = db.get(Market, "market-1")
    assert market is not None
    market.end_date = datetime(2025, 1, 1, tzinfo=UTC)
    market.is_closed = True
    db.commit()
    db.close()

    response = client.get("/api/market/market-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["market_status"] == "closed"
    assert payload["resolves_in_days"] is None


def test_market_detail_not_found(client: TestClient) -> None:
    response = client.get("/api/market/missing")
    assert response.status_code == 404
