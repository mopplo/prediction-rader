"""signal quality metadata

Revision ID: 0002_signal_quality
Revises: 0001_initial
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_signal_quality"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("markets", sa.Column("event_id", sa.String(length=64), nullable=True))
    op.add_column("markets", sa.Column("event_title", sa.Text(), nullable=True))
    op.add_column("markets", sa.Column("tags", sa.Text(), nullable=True))
    op.add_column("markets", sa.Column("market_created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("markets", sa.Column("eligibility_status", sa.String(length=32), nullable=True))
    op.add_column("markets", sa.Column("eligibility_reason", sa.Text(), nullable=True))
    op.create_index("ix_markets_event_id", "markets", ["event_id"], unique=False)
    op.create_index("ix_markets_eligibility_status", "markets", ["eligibility_status"], unique=False)

    op.add_column("signals", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("signals", sa.Column("signal_reason", sa.Text(), nullable=True))
    op.add_column("signals", sa.Column("probability_component", sa.Float(), nullable=True))
    op.add_column("signals", sa.Column("volume_component", sa.Float(), nullable=True))
    op.add_column("signals", sa.Column("liquidity_component", sa.Float(), nullable=True))
    op.add_column("signals", sa.Column("persistence_component", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("signals", "persistence_component")
    op.drop_column("signals", "liquidity_component")
    op.drop_column("signals", "volume_component")
    op.drop_column("signals", "probability_component")
    op.drop_column("signals", "signal_reason")
    op.drop_column("signals", "confidence")
    op.drop_index("ix_markets_eligibility_status", table_name="markets")
    op.drop_index("ix_markets_event_id", table_name="markets")
    op.drop_column("markets", "eligibility_reason")
    op.drop_column("markets", "eligibility_status")
    op.drop_column("markets", "market_created_at")
    op.drop_column("markets", "tags")
    op.drop_column("markets", "event_title")
    op.drop_column("markets", "event_id")
