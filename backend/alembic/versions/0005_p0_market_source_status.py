"""p0 market source and status

Revision ID: 0005_p0_market_source_status
Revises: 0004_v11_metrics_narratives
Create Date: 2026-07-21
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_p0_market_source_status"
down_revision = "0004_v11_metrics_narratives"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("markets", sa.Column("event_slug", sa.String(length=255), nullable=True))
    op.add_column("markets", sa.Column("is_active", sa.Boolean(), nullable=True))
    op.add_column("markets", sa.Column("is_closed", sa.Boolean(), nullable=True))
    op.create_index("ix_markets_event_slug", "markets", ["event_slug"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_markets_event_slug", table_name="markets")
    op.drop_column("markets", "is_closed")
    op.drop_column("markets", "is_active")
    op.drop_column("markets", "event_slug")
