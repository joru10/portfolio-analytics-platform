"""create core ledger tables

Revision ID: 20260215_0002
Revises: 20260215_0001
Create Date: 2026-02-15 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260215_0002"
down_revision = "20260215_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("asset_class", sa.String(length=64), nullable=False, server_default="EQUITY"),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.Column("country", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("symbol", name="uq_instruments_symbol"),
    )
    op.create_index("ix_instruments_symbol", "instruments", ["symbol"])

    op.create_table(
        "prices_eod",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("price_date", sa.Date(), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="provider"),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("symbol", "price_date", name="uq_prices_eod_symbol_date"),
    )
    op.create_index("ix_prices_eod_symbol", "prices_eod", ["symbol"])
    op.create_index("ix_prices_eod_price_date", "prices_eod", ["price_date"])

    op.create_table(
        "positions_snapshot",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("account", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("avg_cost", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("market_price", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("market_value", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("unrealized_pnl", sa.Numeric(precision=18, scale=6), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("snapshot_date", "account", "symbol", name="uq_positions_snapshot_date_account_symbol"),
    )
    op.create_index("ix_positions_snapshot_snapshot_date", "positions_snapshot", ["snapshot_date"])
    op.create_index("ix_positions_snapshot_account", "positions_snapshot", ["account"])
    op.create_index("ix_positions_snapshot_symbol", "positions_snapshot", ["symbol"])

    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("run_details", sa.Text(), nullable=True),
    )
    op.create_index("ix_job_runs_job_name", "job_runs", ["job_name"])
    op.create_index("ix_job_runs_status", "job_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_job_runs_status", table_name="job_runs")
    op.drop_index("ix_job_runs_job_name", table_name="job_runs")
    op.drop_table("job_runs")

    op.drop_index("ix_positions_snapshot_symbol", table_name="positions_snapshot")
    op.drop_index("ix_positions_snapshot_account", table_name="positions_snapshot")
    op.drop_index("ix_positions_snapshot_snapshot_date", table_name="positions_snapshot")
    op.drop_table("positions_snapshot")

    op.drop_index("ix_prices_eod_price_date", table_name="prices_eod")
    op.drop_index("ix_prices_eod_symbol", table_name="prices_eod")
    op.drop_table("prices_eod")

    op.drop_index("ix_instruments_symbol", table_name="instruments")
    op.drop_table("instruments")
