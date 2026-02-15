import json
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_data.factory import get_market_data_provider, resolve_provider_chain
from app.models import JobRun, PriceEOD, Trade


@dataclass
class PriceRefreshResult:
    provider: str
    providers_used: list[str]
    price_date: date
    requested_count: int
    processed_count: int
    failed_symbols: list[str]
    job_run_id: int


def refresh_prices(
    db: Session,
    price_date: date,
    symbols: list[str] | None = None,
    providers: list[str] | None = None,
) -> PriceRefreshResult:
    provider_chain = resolve_provider_chain(providers)

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
                "providers": provider_chain,
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
            provider=provider_chain[0],
            providers_used=provider_chain,
            price_date=price_date,
            requested_count=0,
            processed_count=0,
            failed_symbols=[],
            job_run_id=job_run.id,
        )

    pending = list(requested_symbols)
    points_by_symbol: dict[str, tuple[str, object]] = {}

    for provider_name in provider_chain:
        if not pending:
            break
        provider = get_market_data_provider(provider_name)
        points, failed = provider.fetch_eod(pending, price_date)

        for point in points:
            points_by_symbol[point.symbol] = (provider_name, point)

        failed_set = set(failed)
        pending = [symbol for symbol in pending if symbol in failed_set]

    points = [point for _, point in points_by_symbol.values()]
    existing_rows = db.scalars(
        select(PriceEOD).where(PriceEOD.symbol.in_([point.symbol for point in points]), PriceEOD.price_date == price_date)
    ).all()
    existing_map = {(row.symbol, row.price_date): row for row in existing_rows}

    processed = 0
    for symbol, (provider_name, point) in points_by_symbol.items():
        key = (symbol, point.price_date)
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
    job_run.status = "SUCCESS" if not pending else "PARTIAL_FAILED"
    job_run.run_details = json.dumps(
        {
            "providers": provider_chain,
            "price_date": price_date.isoformat(),
            "requested_symbols": requested_symbols,
            "failed_symbols": pending,
        }
    )
    db.commit()

    return PriceRefreshResult(
        provider=provider_chain[0],
        providers_used=provider_chain,
        price_date=price_date,
        requested_count=len(requested_symbols),
        processed_count=processed,
        failed_symbols=pending,
        job_run_id=job_run.id,
    )
