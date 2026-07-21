"""v1.1 market metrics and narratives

Revision ID: 0004_v11_metrics_narratives
Revises: 0003_dedupe_constraints
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_v11_metrics_narratives"
down_revision = "0003_dedupe_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("markets", sa.Column("condition_id", sa.String(length=128), nullable=True))
    op.add_column("markets", sa.Column("group_item_id", sa.String(length=128), nullable=True))
    op.add_column("markets", sa.Column("topic_key", sa.String(length=255), nullable=True))
    op.create_index("ix_markets_topic_key", "markets", ["topic_key"], unique=False)
    op.create_index("ix_markets_group_item_id", "markets", ["group_item_id"], unique=False)

    op.add_column("market_snapshots", sa.Column("liquidity", sa.Float(), nullable=True))

    op.create_table(
        "market_metrics",
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("change_1h", sa.Float(), nullable=True),
        sa.Column("change_24h", sa.Float(), nullable=True),
        sa.Column("change_7d", sa.Float(), nullable=True),
        sa.Column("volume_spike", sa.Float(), nullable=True),
        sa.Column("signal_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attention_score", sa.Float(), nullable=True),
        sa.Column("market_significance", sa.Float(), nullable=True),
        sa.Column("data_confidence", sa.Float(), nullable=True),
        sa.Column("signal_reason", sa.Text(), nullable=True),
        sa.Column("why_it_moved", sa.Text(), nullable=True),
        sa.Column("probability_component", sa.Float(), nullable=True),
        sa.Column("volume_component", sa.Float(), nullable=True),
        sa.Column("liquidity_component", sa.Float(), nullable=True),
        sa.Column("persistence_component", sa.Float(), nullable=True),
        sa.Column("has_24h_history", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_7d_history", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("history_coverage_hours", sa.Float(), nullable=True),
        sa.Column("eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["markets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("market_id"),
    )
    op.create_index("ix_market_metrics_computed_at", "market_metrics", ["computed_at"], unique=False)
    op.create_index("ix_market_metrics_signal_score", "market_metrics", ["signal_score"], unique=False)

    op.create_table(
        "narratives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic_key", sa.String(length=255), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("market_count", sa.Integer(), nullable=False),
        sa.Column("active_count", sa.Integer(), nullable=False),
        sa.Column("median_abs_change_24h", sa.Float(), nullable=True),
        sa.Column("aggregate_volume_spike", sa.Float(), nullable=True),
        sa.Column("direction_coherence", sa.Float(), nullable=True),
        sa.Column("dominant_direction", sa.String(length=16), nullable=True),
        sa.Column("narrative_score", sa.Float(), nullable=False),
        sa.Column("representative_market_id", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["representative_market_id"], ["markets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_narratives_topic_key", "narratives", ["topic_key"], unique=False)
    op.create_index("ix_narratives_computed_at", "narratives", ["computed_at"], unique=False)

    op.create_table(
        "narrative_members",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("narrative_id", sa.Integer(), nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["markets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["narrative_id"], ["narratives.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("narrative_id", "market_id", name="uq_narrative_member"),
    )


def downgrade() -> None:
    op.drop_table("narrative_members")
    op.drop_table("narratives")
    op.drop_index("ix_market_metrics_signal_score", table_name="market_metrics")
    op.drop_index("ix_market_metrics_computed_at", table_name="market_metrics")
    op.drop_table("market_metrics")
    op.drop_column("market_snapshots", "liquidity")
    op.drop_index("ix_markets_group_item_id", table_name="markets")
    op.drop_index("ix_markets_topic_key", table_name="markets")
    op.drop_column("markets", "topic_key")
    op.drop_column("markets", "group_item_id")
    op.drop_column("markets", "condition_id")
