"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "markets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("yes_token_id", sa.String(length=128), nullable=True),
        sa.Column("current_probability", sa.Float(), nullable=True),
        sa.Column("volume_24h", sa.Float(), nullable=True),
        sa.Column("volume_1wk", sa.Float(), nullable=True),
        sa.Column("liquidity", sa.Float(), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_markets_slug", "markets", ["slug"], unique=False)
    op.create_index("ix_markets_yes_token_id", "markets", ["yes_token_id"], unique=False)

    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("volume_24h", sa.Float(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["markets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_snapshots_captured_at", "market_snapshots", ["captured_at"], unique=False)
    op.create_index("ix_market_snapshots_market_captured", "market_snapshots", ["market_id", "captured_at"], unique=False)

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("signal_type", sa.String(length=32), nullable=False),
        sa.Column("change_1h", sa.Float(), nullable=True),
        sa.Column("change_24h", sa.Float(), nullable=True),
        sa.Column("change_7d", sa.Float(), nullable=True),
        sa.Column("volume_spike", sa.Float(), nullable=True),
        sa.Column("signal_score", sa.Float(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["market_id"], ["markets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signals_computed_at", "signals", ["computed_at"], unique=False)
    op.create_index("ix_signals_market_computed", "signals", ["market_id", "computed_at"], unique=False)
    op.create_index("ix_signals_signal_type", "signals", ["signal_type"], unique=False)
    op.create_index("ix_signals_type_score", "signals", ["signal_type", "signal_score"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_signals_type_score", table_name="signals")
    op.drop_index("ix_signals_signal_type", table_name="signals")
    op.drop_index("ix_signals_market_computed", table_name="signals")
    op.drop_index("ix_signals_computed_at", table_name="signals")
    op.drop_table("signals")
    op.drop_index("ix_market_snapshots_market_captured", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_captured_at", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_index("ix_markets_yes_token_id", table_name="markets")
    op.drop_index("ix_markets_slug", table_name="markets")
    op.drop_table("markets")
