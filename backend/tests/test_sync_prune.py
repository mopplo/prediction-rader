from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db import Base
from app.models import Market, MarketSnapshot
from app.services.sync import SyncService


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_prune_old_snapshots_keeps_recent_rows(db_session) -> None:
    now = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
    db_session.add(
        Market(
            id="market-1",
            title="Will GPT-6 be released before 2027?",
            current_probability=0.5,
            eligibility_status="eligible",
        )
    )
    db_session.add_all(
        [
            MarketSnapshot(
                market_id="market-1",
                probability=0.4,
                captured_at=now - timedelta(days=8),
            ),
            MarketSnapshot(
                market_id="market-1",
                probability=0.45,
                captured_at=now - timedelta(days=7, minutes=1),
            ),
            MarketSnapshot(
                market_id="market-1",
                probability=0.5,
                captured_at=now - timedelta(days=3),
            ),
            MarketSnapshot(
                market_id="market-1",
                probability=0.55,
                captured_at=now,
            ),
        ]
    )
    db_session.commit()

    service = SyncService(db_session)
    service.settings = Settings(snapshot_retention_days=7)
    pruned = service._prune_old_snapshots(now)
    db_session.commit()

    assert pruned == 2
    remaining = db_session.scalars(
        select(MarketSnapshot).order_by(MarketSnapshot.captured_at.asc())
    ).all()
    assert len(remaining) == 2
    assert [snapshot.probability for snapshot in remaining] == [0.5, 0.55]


def test_prune_old_snapshots_respects_custom_retention(db_session) -> None:
    now = datetime(2026, 7, 23, 12, 0, tzinfo=UTC)
    db_session.add(
        Market(
            id="market-2",
            title="Fed cut rates?",
            current_probability=0.4,
            eligibility_status="eligible",
        )
    )
    db_session.add_all(
        [
            MarketSnapshot(
                market_id="market-2",
                probability=0.3,
                captured_at=now - timedelta(days=4),
            ),
            MarketSnapshot(
                market_id="market-2",
                probability=0.35,
                captured_at=now - timedelta(days=2),
            ),
        ]
    )
    db_session.commit()

    service = SyncService(db_session)
    service.settings = Settings(snapshot_retention_days=3)
    pruned = service._prune_old_snapshots(now)
    db_session.commit()

    assert pruned == 1
    remaining = db_session.scalars(select(MarketSnapshot)).all()
    assert len(remaining) == 1
    assert remaining[0].probability == 0.35
