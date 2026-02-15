import json
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_data.factory import get_market_data_provider
from app.models import JobRun, PriceEOD, Trade


@dataclass
class PriceRefreshResult:
    provider: str
    price_date: date
    requested_count: int
    processed_count: int
    failed_symbols: list[str]
    job_run_id: int


def refresh_prices(db: Session, price_date: date, symbols: list[str] | None = None) -> PriceRefreshResult:
    provider = get_market_data_provider()
    provider_name = provider.__class__.__name__

    requested_symbols = sorted({symbol.strip().upper() for symbol in (symbols or []) if symbol.strip()})
    if not requested_symbols:
        requested_symbols = sorted(set(db.scalars(select(Trade.symbol)).all()))

    job_run = JobRun(
        job_name="price_refresh",
        status="RUNNING",
        started_at=datetime.now(UTC),
        rows_processed=0,
        run_details=json.dumps(
            {
                "provider": provider_name,
                "price_date": price_date.isoformat(),
                "requested_symbols": requested_symbols,
            }
        ),
    )
    db.add(job_run)
    db.flush()

    if not requested_symbols:
        job_run.status = "SUCCESS"
        db.commit()
        return PriceRefreshResult(
            provider=provider_name,
            price_date=price_date,
            requested_count=0,
            processed_count=0,
            failed_symbols=[],
            job_run_id=job_run.id,
        )

    points, failed = provider.fetch_eod(requested_symbols, price_date)

    existing_rows = db.scalars(
        select(PriceEOD).where(PriceEOD.symbol.in_([point.symbol for point in points]), PriceEOD.price_date == price_date)
    ).all()
    existing_map = {(row.symbol, row.price_date): row for row in existing_rows}

    processed = 0
    for point in points:
        key = (point.symbol, point.price_date)
        row = existing_map.get(key)
        if row:
            row.close_price = point.close_price
            row.currency = point.currency
            row.source = provider_name
        else:
            db.add(
                PriceEOD(
                    symbol=point.symbol,
                    price_date=point.price_date,
                    close_price=point.close_price,
                    currency=point.currency,
                    source=provider_name,
                    ingested_at=datetime.now(UTC),
                )
            )
        processed += 1

    job_run.rows_processed = processed
    job_run.status = "SUCCESS" if not failed else "PARTIAL_FAILED"
    job_run.run_details = json.dumps(
        {
            "provider": provider_name,
            "price_date": price_date.isoformat(),
            "requested_symbols": requested_symbols,
            "failed_symbols": failed,
        }
    )
    db.commit()

    return PriceRefreshResult(
        provider=provider_name,
        price_date=price_date,
        requested_count=len(requested_symbols),
        processed_count=processed,
        failed_symbols=failed,
        job_run_id=job_run.id,
    )
