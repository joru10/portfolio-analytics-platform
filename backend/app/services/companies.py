import math
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_data.factory import get_market_data_provider, resolve_provider_chain
from app.models import PriceEOD


@dataclass
class CompanyComparePoint:
    date: date
    prices: dict[str, float | None]
    normalized: dict[str, float | None]


@dataclass
class CompanyCompareSummary:
    symbol: str
    start_price: float | None
    end_price: float | None
    return_pct: float
    annualized_volatility: float
    max_drawdown: float
    observations: int


@dataclass
class CompanyCompareResult:
    start_date: date
    end_date: date
    symbols: list[str]
    providers_used: list[str]
    failed_symbols: list[str]
    series: list[CompanyComparePoint]
    summary: list[CompanyCompareSummary]
    correlation: dict[str, dict[str, float]]


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _max_drawdown(prices: list[float]) -> float:
    if not prices:
        return 0.0
    peak = prices[0]
    max_dd = 0.0
    for px in prices:
        peak = max(peak, px)
        if peak > 0:
            max_dd = min(max_dd, (px / peak) - 1.0)
    return max_dd


def _pearson(x: list[float], y: list[float]) -> float:
    if len(x) < 2 or len(y) < 2 or len(x) != len(y):
        return 0.0

    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y, strict=True))
    var_x = sum((a - mean_x) ** 2 for a in x)
    var_y = sum((b - mean_y) ** 2 for b in y)
    if var_x <= 0 or var_y <= 0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)


def _normalize_symbols(symbols: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for raw in symbols:
        clean = raw.strip().upper()
        if clean and clean not in seen:
            seen.add(clean)
            deduped.append(clean)
    return deduped


def compare_companies(
    db: Session,
    symbols: list[str],
    start_date: date,
    end_date: date,
    providers: list[str] | None = None,
) -> CompanyCompareResult:
    clean_symbols = _normalize_symbols(symbols)
    if not clean_symbols:
        raise ValueError("At least one symbol is required")

    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    if (end_date - start_date).days > 730:
        raise ValueError("Date range too wide; use 730 days or fewer")

    provider_chain = resolve_provider_chain(providers)

    pending = list(clean_symbols)
    points_by_key: dict[tuple[str, date], tuple[str, Decimal, str]] = {}

    for provider_name in provider_chain:
        if not pending:
            break

        provider = get_market_data_provider(provider_name)
        points, failed = provider.fetch_history(pending, start_date, end_date)

        succeeded_symbols: set[str] = set()
        for point in points:
            key = (point.symbol, point.price_date)
            points_by_key[key] = (provider_name, point.close_price, point.currency)
            succeeded_symbols.add(point.symbol)

        failed_set = {symbol.strip().upper() for symbol in failed}
        pending = [sym for sym in pending if sym not in succeeded_symbols and sym in failed_set]

    if points_by_key:
        keys = list(points_by_key.keys())
        existing_rows = db.scalars(
            select(PriceEOD).where(
                PriceEOD.symbol.in_([symbol for symbol, _ in keys]),
                PriceEOD.price_date.in_([dt for _, dt in keys]),
            )
        ).all()
        existing_map = {(row.symbol, row.price_date): row for row in existing_rows}

        for (symbol, dt), (source, close_price, currency) in points_by_key.items():
            row = existing_map.get((symbol, dt))
            if row:
                row.close_price = close_price
                row.currency = currency
                row.source = source
            else:
                db.add(
                    PriceEOD(
                        symbol=symbol,
                        price_date=dt,
                        close_price=close_price,
                        currency=currency,
                        source=source,
                        ingested_at=datetime.now(UTC),
                    )
                )
        db.commit()

    rows = db.scalars(
        select(PriceEOD)
        .where(
            PriceEOD.symbol.in_(clean_symbols),
            PriceEOD.price_date >= start_date,
            PriceEOD.price_date <= end_date,
        )
        .order_by(PriceEOD.price_date, PriceEOD.symbol)
    ).all()

    timeline = sorted({row.price_date for row in rows})

    prices_by_date: dict[date, dict[str, float | None]] = {}
    for dt in timeline:
        prices_by_date[dt] = {symbol: None for symbol in clean_symbols}
    for row in rows:
        prices_by_date[row.price_date][row.symbol] = float(row.close_price)

    first_price: dict[str, float | None] = {symbol: None for symbol in clean_symbols}
    series: list[CompanyComparePoint] = []
    for dt in timeline:
        price_row = prices_by_date[dt]
        norm_row: dict[str, float | None] = {}
        for symbol in clean_symbols:
            px = price_row.get(symbol)
            if px is not None and first_price[symbol] is None:
                first_price[symbol] = px
            base = first_price[symbol]
            norm_row[symbol] = (px / base) if (px is not None and base and base > 0) else None
        series.append(CompanyComparePoint(date=dt, prices=price_row, normalized=norm_row))

    summary: list[CompanyCompareSummary] = []
    returns_by_symbol: dict[str, dict[date, float]] = {}

    for symbol in clean_symbols:
        symbol_prices = [(dt, prices_by_date[dt][symbol]) for dt in timeline if prices_by_date[dt][symbol] is not None]
        clean_series = [(dt, float(px)) for dt, px in symbol_prices if px is not None]

        if len(clean_series) >= 2:
            start_price = clean_series[0][1]
            end_price = clean_series[-1][1]
            return_pct = (end_price / start_price) - 1.0 if start_price > 0 else 0.0

            daily_returns: list[float] = []
            for idx in range(1, len(clean_series)):
                prev_px = clean_series[idx - 1][1]
                cur_px = clean_series[idx][1]
                if prev_px > 0:
                    ret = (cur_px / prev_px) - 1.0
                    daily_returns.append(ret)
                    returns_by_symbol.setdefault(symbol, {})[clean_series[idx][0]] = ret

            annualized_volatility = _stddev(daily_returns) * math.sqrt(252) if daily_returns else 0.0
            max_drawdown = _max_drawdown([px for _, px in clean_series])
        elif len(clean_series) == 1:
            start_price = clean_series[0][1]
            end_price = clean_series[0][1]
            return_pct = 0.0
            annualized_volatility = 0.0
            max_drawdown = 0.0
        else:
            start_price = None
            end_price = None
            return_pct = 0.0
            annualized_volatility = 0.0
            max_drawdown = 0.0

        summary.append(
            CompanyCompareSummary(
                symbol=symbol,
                start_price=start_price,
                end_price=end_price,
                return_pct=return_pct,
                annualized_volatility=annualized_volatility,
                max_drawdown=max_drawdown,
                observations=len(clean_series),
            )
        )

    symbols_with_data = {item.symbol for item in summary if item.observations > 0}
    failed_symbols = [symbol for symbol in clean_symbols if symbol not in symbols_with_data]

    correlation: dict[str, dict[str, float]] = {}
    for left in clean_symbols:
        correlation[left] = {}
        for right in clean_symbols:
            if left == right:
                correlation[left][right] = 1.0
                continue

            left_returns = returns_by_symbol.get(left, {})
            right_returns = returns_by_symbol.get(right, {})
            shared_dates = sorted(set(left_returns.keys()) & set(right_returns.keys()))
            if len(shared_dates) < 2:
                correlation[left][right] = 0.0
                continue

            x = [left_returns[dt] for dt in shared_dates]
            y = [right_returns[dt] for dt in shared_dates]
            correlation[left][right] = _pearson(x, y)

    return CompanyCompareResult(
        start_date=start_date,
        end_date=end_date,
        symbols=clean_symbols,
        providers_used=provider_chain,
        failed_symbols=failed_symbols,
        series=series,
        summary=summary,
        correlation=correlation,
    )
