from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from app.models import Base


def test_core_schema_tables_and_indexes_exist() -> None:
    engine = create_engine(
        "sqlite+pysqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert {"trades", "instruments", "prices_eod", "positions_snapshot", "job_runs"}.issubset(tables)

    positions_indexes = {idx["name"] for idx in inspector.get_indexes("positions_snapshot")}
    assert "ix_positions_snapshot_snapshot_date" in positions_indexes
    assert "ix_positions_snapshot_account" in positions_indexes
    assert "ix_positions_snapshot_symbol" in positions_indexes

    price_uniques = {u["name"] for u in inspector.get_unique_constraints("prices_eod")}
    assert "uq_prices_eod_symbol_date" in price_uniques
