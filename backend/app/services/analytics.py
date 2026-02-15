import math
from dataclasses import dataclass
from datetime import date
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PriceEOD, Trade
from app.services.portfolio import calculate_positions


@dataclass
class AnalyticsPoint:
    date: date
    market_value: float
    total_pnl: float
    daily_return: float
    cumulative_return: float
    drawdown: float


@dataclass
class AnalyticsResult:
    snapshot_date: date
    start_date: date
    account_filter: str | None
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    concentration_top_symbol: str | None
    concentration_top_weight: float
    series: list[AnalyticsPoint]


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    var = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(var)


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * p))))
    return ordered[idx]


def calculate_analytics(
    db: Session,
    snapshot_date: date,
    account: str | None = None,
    start_date: date | None = None,
) -> AnalyticsResult:
    trade_query = select(Trade).where(Trade.trade_date <= snapshot_date)
    if account:
        trade_query = trade_query.where(Trade.account == account)

    trades = db.scalars(trade_query.order_by(Trade.trade_date, Trade.id)).all()
    if not trades:
        return AnalyticsResult(
            snapshot_date=snapshot_date,
            start_date=start_date or snapshot_date,
            account_filter=account,
            annualized_volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            var_95=0.0,
            cvar_95=0.0,
            concentration_top_symbol=None,
            concentration_top_weight=0.0,
            series=[],
        )

    symbols = sorted({trade.symbol for trade in trades})
    min_trade_date = min(trade.trade_date for trade in trades)
    effective_start = start_date or min_trade_date
    if effective_start > snapshot_date:
        effective_start = snapshot_date

    price_dates = db.scalars(
        select(PriceEOD.price_date)
        .where(
            PriceEOD.symbol.in_(symbols),
            PriceEOD.price_date >= effective_start,
            PriceEOD.price_date <= snapshot_date,
        )
        .distinct()
        .order_by(PriceEOD.price_date)
    ).all()

    timeline = sorted({d for d in price_dates if d >= effective_start and d <= snapshot_date})
    if not timeline:
        timeline = [snapshot_date]

    points: list[AnalyticsPoint] = []
    prev_market = 0.0
    base_market = None
    running_peak = 0.0

    for dt in timeline:
        positions = calculate_positions(db=db, snapshot_date=dt, account=account)
        market_value = sum(float(pos.market_value or 0) for pos in positions)
        total_pnl = sum(float((pos.unrealized_pnl or 0) + pos.realized_pnl) for pos in positions)

        if prev_market > 0:
            daily_return = (market_value / prev_market) - 1.0
        else:
            daily_return = 0.0

        if base_market is None and market_value > 0:
            base_market = market_value
        cumulative_return = ((market_value / base_market) - 1.0) if (base_market and base_market > 0) else 0.0

        running_peak = max(running_peak, market_value)
        drawdown = ((market_value - running_peak) / running_peak) if running_peak > 0 else 0.0

        points.append(
            AnalyticsPoint(
                date=dt,
                market_value=market_value,
                total_pnl=total_pnl,
                daily_return=daily_return,
                cumulative_return=cumulative_return,
                drawdown=drawdown,
            )
        )
        prev_market = market_value

    daily_returns = [p.daily_return for p in points[1:]]
    daily_vol = _stddev(daily_returns)
    annualized_vol = daily_vol * math.sqrt(252)
    avg_daily = mean(daily_returns) if daily_returns else 0.0
    sharpe = (avg_daily / daily_vol) * math.sqrt(252) if daily_vol > 0 else 0.0
    max_drawdown = min((p.drawdown for p in points), default=0.0)

    var_95 = _percentile(daily_returns, 0.05) if daily_returns else 0.0
    tail = [r for r in daily_returns if r <= var_95]
    cvar_95 = (sum(tail) / len(tail)) if tail else var_95

    latest_positions = calculate_positions(db=db, snapshot_date=snapshot_date, account=account)
    exposure = [
        (pos.symbol, float(pos.market_value or 0))
        for pos in latest_positions
        if float(pos.market_value or 0) > 0
    ]
    total_exposure = sum(v for _, v in exposure)
    if exposure and total_exposure > 0:
        top_symbol, top_value = max(exposure, key=lambda t: t[1])
        top_weight = top_value / total_exposure
    else:
        top_symbol, top_weight = None, 0.0

    return AnalyticsResult(
        snapshot_date=snapshot_date,
        start_date=effective_start,
        account_filter=account,
        annualized_volatility=annualized_vol,
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        var_95=var_95,
        cvar_95=cvar_95,
        concentration_top_symbol=top_symbol,
        concentration_top_weight=top_weight,
        series=points,
    )
