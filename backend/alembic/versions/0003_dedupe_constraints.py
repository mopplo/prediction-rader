"""dedupe constraints for signals and snapshots

Revision ID: 0003_dedupe_constraints
Revises: 0002_signal_quality
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_dedupe_constraints"
down_revision = "0002_signal_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM signals s
        USING signals newer
        WHERE s.market_id = newer.market_id
          AND s.signal_type = newer.signal_type
          AND s.id < newer.id
        """
    )
    op.execute(
        """
        DELETE FROM market_snapshots s
        USING market_snapshots newer
        WHERE s.market_id = newer.market_id
          AND s.captured_at = newer.captured_at
          AND s.id < newer.id
        """
    )
    op.create_unique_constraint(
        "uq_signals_market_type",
        "signals",
        ["market_id", "signal_type"],
    )
    op.create_unique_constraint(
        "uq_snapshots_market_captured",
        "market_snapshots",
        ["market_id", "captured_at"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_snapshots_market_captured", "market_snapshots", type_="unique")
    op.drop_constraint("uq_signals_market_type", "signals", type_="unique")
